import { GoogleGenAI, type LiveServerMessage, type Session } from '@google/genai'
import { MicrophoneStreamer, PcmPlayer } from './audio-pcm'

export type GeminiLiveStatus = 'idle' | 'connecting' | 'connected' | 'listening' | 'speaking' | 'error'

export interface GeminiLiveCallbacks {
  onStatus: (status: GeminiLiveStatus) => void
  onBotText: (text: string) => void
  onUserText: (text: string) => void
  onError: (message: string) => void
  onFieldUpdate: (fieldId: string, value: unknown) => Promise<Record<string, unknown>>
  onBatchFieldUpdate?: (fields: Record<string, unknown>) => Promise<Record<string, unknown>>
}

function parseToolValue(raw: string): unknown {
  try {
    return JSON.parse(raw)
  } catch {
    return raw
  }
}

function extractInlineAudio(message: LiveServerMessage): string | null {
  const parts = message.serverContent?.modelTurn?.parts
  if (!parts) return null

  for (const part of parts) {
    const data = part.inlineData?.data
    const mime = part.inlineData?.mimeType ?? ''
    if (data && mime.includes('audio')) {
      return data
    }
  }
  return null
}

export class GeminiLiveSession {
  private session: Session | null = null
  private mic: MicrophoneStreamer | null = null
  private player: PcmPlayer | null = null
  private closed = false
  private ready = false
  private openingPending = false
  private openingDone = false
  private openingTurnComplete = false
  private heardBotOutput = false
  private resolveOpening: (() => void) | null = null
  private openingTimeout: ReturnType<typeof setTimeout> | null = null
  private toolCallPending = false

  private canUseTools(): boolean {
    return !this.closed && this.ready && this.session !== null
  }

  private canSendAudio(): boolean {
    return this.canUseTools() && this.openingDone
  }

  private canSendVideo(): boolean {
    return this.canUseTools() && !this.toolCallPending
  }

  sendVideoFrame(base64Jpeg: string) {
    if (!this.canSendVideo() || !this.session || !base64Jpeg) return

    try {
      this.session.sendRealtimeInput({
        video: {
          data: base64Jpeg,
          mimeType: 'image/jpeg',
        },
      })
    } catch {
      void this.disconnect()
    }
  }

  private sendAudioChunk(base64Pcm: string) {
    if (!this.canSendAudio() || this.toolCallPending || !this.session) return

    try {
      this.session.sendRealtimeInput({
        audio: {
          data: base64Pcm,
          mimeType: 'audio/pcm;rate=16000',
        },
      })
    } catch {
      void this.disconnect()
    }
  }

  private clearOpeningTimeout() {
    if (this.openingTimeout) {
      clearTimeout(this.openingTimeout)
      this.openingTimeout = null
    }
  }

  private finishOpening() {
    if (this.openingDone) return
    this.openingDone = true
    this.openingPending = false
    this.clearOpeningTimeout()
    this.resolveOpening?.()
    this.resolveOpening = null
  }

  private async tryFinishOpening() {
    if (this.openingDone || !this.openingPending) return
    if (!this.openingTurnComplete || !this.heardBotOutput) return

    await this.player?.waitForPlaybackDone(500)
    this.finishOpening()
  }

  private triggerOpeningTurn(session: Session) {
    if (this.openingPending || this.closed) return
    this.openingPending = true

    // Gemini 3.1: use sendRealtimeInput for in-session text (not sendClientContent).
    session.sendRealtimeInput({
      text: 'Session connected. Live webcam is ON — patient may show ID/passport/license/insurance on camera; use scan_document_fields when they ask you to read it. Save with update_form_field first. After each answer: vary brief ack or skip ack, then next question. Never repeat the same ack every turn. Never say is that correct per field. START SPEAKING NOW in English: greet, mention they can show documents to the camera, then ask first field.',
    })

    this.openingTimeout = setTimeout(() => {
      void this.tryFinishOpeningForced()
    }, 25000)
  }

  private async tryFinishOpeningForced() {
    if (this.openingDone) return
    if (!this.heardBotOutput) return
    await this.player?.waitForPlaybackDone(500)
    this.finishOpening()
  }

  private async startMicrophone(callbacks: GeminiLiveCallbacks) {
    if (this.closed || this.mic) return

    this.mic = new MicrophoneStreamer()
    await this.mic.start((base64Pcm) => this.sendAudioChunk(base64Pcm))
    callbacks.onStatus('listening')
  }

  async connect(token: string, model: string, callbacks: GeminiLiveCallbacks): Promise<void> {
    await this.disconnect()

    this.closed = false
    this.ready = false
    this.toolCallPending = false
    this.openingPending = false
    this.openingDone = false
    this.openingTurnComplete = false
    this.heardBotOutput = false
    callbacks.onStatus('connecting')

    const ai = new GoogleGenAI({
      apiKey: token,
      httpOptions: { apiVersion: 'v1alpha' },
    })

    this.player = new PcmPlayer(24000)
    await this.player.resume()

    let resolveReady: (() => void) | null = null
    let rejectReady: ((error: Error) => void) | null = null
    let readySettled = false

    const settleReady = (resolve: boolean, error?: Error) => {
      if (readySettled) return
      readySettled = true
      if (resolve) resolveReady?.()
      else rejectReady?.(error ?? new Error('Gemini Live connection failed'))
    }

    const readyPromise = new Promise<void>((resolve, reject) => {
      resolveReady = resolve
      rejectReady = reject
    })

    const openingPromise = new Promise<void>((resolve) => {
      this.resolveOpening = resolve
    })

    try {
      this.session = await ai.live.connect({
        model,
        callbacks: {
          onmessage: async (message: LiveServerMessage) => {
            if (this.closed) return

            if (message.setupComplete && !this.ready) {
              this.ready = true
              callbacks.onStatus('connected')
              settleReady(true)
              if (this.session) {
                this.triggerOpeningTurn(this.session)
              }
              return
            }

            const inputText = message.serverContent?.inputTranscription?.text
            if (inputText) {
              callbacks.onUserText(inputText)
            }

            const outputText =
              message.serverContent?.outputTranscription?.text ?? message.text ?? undefined
            if (outputText) {
              this.heardBotOutput = true
              callbacks.onBotText(outputText)
              callbacks.onStatus('speaking')
              void this.tryFinishOpening()
            }

            const audio = extractInlineAudio(message)
            if (audio) {
              this.heardBotOutput = true
              this.player?.playBase64Pcm(audio)
              callbacks.onStatus('speaking')
            }

            const turnDone =
              message.serverContent?.turnComplete || message.serverContent?.generationComplete
            if (turnDone) {
              if (this.openingPending && !this.openingDone) {
                this.openingTurnComplete = true
                void this.tryFinishOpening()
              } else if (this.mic) {
                callbacks.onStatus('listening')
              }
            }

            const functionCalls = message.toolCall?.functionCalls ?? []
            if (functionCalls.length > 0 && this.session && this.canUseTools()) {
              this.toolCallPending = true
              const responses: Array<{ id: string; name: string; response: Record<string, unknown> }> = []

              try {
                for (const call of functionCalls) {
                  if (!call.id) continue

                  if (call.name === 'update_form_field') {
                    const args = (call.args ?? {}) as { field_id?: string; value?: string }
                    if (!args.field_id) continue

                    const parsedValue = parseToolValue(String(args.value ?? ''))
                    const progress = await callbacks.onFieldUpdate(args.field_id, parsedValue)
                    const instruction =
                      typeof progress.voice_instruction === 'string' ? progress.voice_instruction : ''
                    responses.push({
                      id: call.id,
                      name: call.name,
                      response: {
                        ok: true,
                        voice_instruction: instruction,
                        say_next: progress.say_next ?? null,
                        say_next_en: progress.say_next_en ?? null,
                        say_next_vi: progress.say_next_vi ?? null,
                        ...progress,
                      },
                    })
                    continue
                  }

                  if (call.name === 'scan_document_fields' && callbacks.onBatchFieldUpdate) {
                    const args = (call.args ?? {}) as { fields_json?: string }
                    let fields: Record<string, unknown> = {}
                    try {
                      const parsed = JSON.parse(String(args.fields_json ?? '{}'))
                      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
                        fields = parsed as Record<string, unknown>
                      }
                    } catch {
                      responses.push({
                        id: call.id,
                        name: call.name,
                        response: { ok: false, error: 'Invalid fields_json' },
                      })
                      continue
                    }

                    const progress = await callbacks.onBatchFieldUpdate(fields)
                    responses.push({
                      id: call.id,
                      name: call.name,
                      response: {
                        ok: true,
                        saved_count: Object.keys(fields).length,
                        say_next: progress.say_next ?? null,
                        say_next_en: progress.say_next_en ?? null,
                        say_next_vi: progress.say_next_vi ?? null,
                        ...progress,
                      },
                    })
                  }
                }

                if (responses.length > 0) {
                  this.session.sendToolResponse({ functionResponses: responses })
                  const last = responses[responses.length - 1]?.response
                  const sayNextEn =
                    typeof last?.say_next_en === 'string'
                      ? last.say_next_en
                      : typeof last?.say_next === 'string'
                        ? last.say_next
                        : ''
                  const sayNextVi = typeof last?.say_next_vi === 'string' ? last.say_next_vi : ''
                  const savedCount = typeof last?.saved_count === 'number' ? last.saved_count : 0
                  if (sayNextEn || sayNextVi) {
                    const scanHint =
                      savedCount > 0
                        ? `Document scan saved ${savedCount} field(s). Briefly tell patient what you read, then continue. `
                        : ''
                    this.session.sendRealtimeInput({
                      text: `${scanHint}Speak naturally in patient's language — follow say_next (varied ack OK, or no ack). English: "${sayNextEn}". Vietnamese: "${sayNextVi}". Never say "tôi sẽ ghi vào" every time. No per-field confirmation.`,
                    })
                  }
                }
              } catch (error) {
                const detail = error instanceof Error ? error.message : 'Tool call failed'
                const errorResponses = functionCalls.flatMap((call) => {
                  if (!call.id) return []
                  if (call.name !== 'update_form_field' && call.name !== 'scan_document_fields') return []
                  return [{
                    id: call.id,
                    name: call.name,
                    response: { ok: false, error: detail },
                  }]
                })
                if (errorResponses.length > 0) {
                  this.session.sendToolResponse({ functionResponses: errorResponses })
                }
              } finally {
                this.toolCallPending = false
              }
            }
          },
          onerror: (event: ErrorEvent) => {
            const error = new Error(event.message || 'Gemini Live connection error')
            settleReady(false, error)
            if (!this.closed) {
              callbacks.onStatus('error')
              callbacks.onError(error.message)
            }
            void this.disconnect()
          },
          onclose: (event: CloseEvent) => {
            const reason = event.reason?.trim()
            if (!readySettled) {
              settleReady(
                false,
                new Error(reason || 'Không thể kết nối Gemini Live. Vui lòng thử lại.'),
              )
            } else if (!this.closed && reason) {
              callbacks.onStatus('error')
              callbacks.onError(reason)
            }
            void this.disconnect()
          },
        },
      })

      await Promise.race([
        readyPromise,
        new Promise<void>((_, reject) => {
          setTimeout(() => reject(new Error('Hết thời gian chờ kết nối Gemini Live (15s)')), 15000)
        }),
      ])
    } catch (error) {
      await this.disconnect()
      throw error instanceof Error ? error : new Error('Failed to connect Gemini Live')
    }

    await Promise.race([
      openingPromise,
      new Promise<void>((resolve) => setTimeout(resolve, 25000)),
    ])

    if (!this.openingDone) {
      this.finishOpening()
    }

    if (this.closed) return

    await this.startMicrophone(callbacks)
  }

  async disconnect() {
    if (this.closed && !this.mic && !this.session) return

    this.closed = true
    this.ready = false
    this.toolCallPending = false
    this.clearOpeningTimeout()
    this.finishOpening()

    this.mic?.stop()
    this.mic = null

    const activeSession = this.session
    this.session = null

    try {
      activeSession?.close()
    } catch {
      // Already closed.
    }

    this.player?.stop()
    this.player = null
  }
}
