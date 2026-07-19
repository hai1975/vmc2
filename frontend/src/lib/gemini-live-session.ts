import { GoogleGenAI, type LiveServerMessage, type Session } from '@google/genai'
import type { ProviderLookupResult } from '../types'
import { MicrophoneStreamer, PcmPlayer } from './audio-pcm'

export type GeminiLiveStatus = 'idle' | 'connecting' | 'connected' | 'listening' | 'speaking' | 'error'

export interface GeminiLiveCallbacks {
  onStatus: (status: GeminiLiveStatus) => void
  onBotText: (text: string) => void
  onUserText: (text: string) => void
  onError: (message: string) => void
  onFieldUpdate: (fieldId: string, value: unknown) => Promise<Record<string, unknown>>
  onBatchFieldUpdate?: (fields: Record<string, unknown>) => Promise<Record<string, unknown>>
  onFormSelect?: (dob: string, voiceLanguage: string) => Promise<FormSelectProgress>
  onProviderLookup?: (query: string) => Promise<ProviderLookupResult>
  onNavigatePage?: (
    action: 'next' | 'back' | 'goto',
    page?: number,
  ) => Promise<{ ok: boolean; page: number; total_pages: number }> | { ok: boolean; page: number; total_pages: number }
}

export interface GeminiLiveConnectOptions {
  triage?: boolean
}

export interface FormSelectProgress extends Record<string, unknown> {
  registration_context?: string
}

function parseToolValue(raw: string): unknown {
  try {
    return JSON.parse(raw)
  } catch {
    return raw
  }
}

/** Gemini Live often returns tool args as strings — coerce page numbers safely. */
function parsePageNumber(raw: unknown): number | undefined {
  if (typeof raw === 'number' && Number.isFinite(raw)) return Math.round(raw)
  if (typeof raw === 'string' && raw.trim()) {
    const n = Number.parseFloat(raw.trim().replace(/^goto[_\s-]*/i, ''))
    if (Number.isFinite(n)) return Math.round(n)
  }
  return undefined
}

function parseNavigateAction(raw: unknown): 'next' | 'back' | 'goto' {
  const text = String(raw ?? 'next').toLowerCase().trim()
  if (text === 'back' || text === 'prev' || text === 'previous') return 'back'
  if (text === 'goto' || text === 'go' || text === 'jump' || text.startsWith('goto')) return 'goto'
  // Model sometimes passes the page number as the "action"
  if (/^\d+$/.test(text)) return 'goto'
  return 'next'
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

function isModelRefusalText(text: string): boolean {
  const t = text.toLowerCase()
  return (
    t.includes("just a language model") ||
    t.includes("can't help with that") ||
    t.includes("cannot help with that") ||
    t.includes("i'm unable to help") ||
    t.includes("i am unable to help") ||
    t.includes("as an ai language model")
  )
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
  private triageMode = false

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

    const openingText = this.triageMode
      ? (
          'Session ready. You are the VM Clinic registration assistant — this task is allowed. ' +
          'Speak EXACTLY: "VM Clinic is listening. I can help you register." ' +
          'Then ask ONLY for date of birth. Never say you are just a language model or cannot help. START NOW.'
        )
      : (
          'Session ready for this form section. Continue registration — do NOT greet again. ' +
          'Do NOT say "VM Clinic is listening" or "I can help you register". ' +
          'Ask the first unanswered field for THIS section only. Never refuse. START NOW.'
        )

    session.sendRealtimeInput({ text: openingText })

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

  async connect(
    token: string,
    model: string,
    callbacks: GeminiLiveCallbacks,
    options?: GeminiLiveConnectOptions,
  ): Promise<void> {
    await this.disconnect()

    this.closed = false
    this.ready = false
    this.triageMode = Boolean(options?.triage)
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
              if (isModelRefusalText(outputText)) {
                callbacks.onError(
                  'MODEL_REFUSAL: Bot refused the registration task. Please tap Speak again.',
                )
              }
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
                let formSelected = false
                let registrationContext = ''
                for (const call of functionCalls) {
                  if (!call.id) continue

                  if (call.name === 'select_registration_form' && callbacks.onFormSelect) {
                    const args = (call.args ?? {}) as { dob?: string; voice_language?: string }
                    const progress = await callbacks.onFormSelect(
                      String(args.dob ?? ''),
                      String(args.voice_language ?? 'en'),
                    )
                    if (typeof progress.registration_context === 'string') {
                      registrationContext = progress.registration_context
                    }
                    this.triageMode = false
                    formSelected = true
                    responses.push({
                      id: call.id,
                      name: call.name,
                      response: {
                        ok: true,
                        form_selected: true,
                        say_next: progress.say_next ?? null,
                        say_next_en: progress.say_next_en ?? null,
                        say_next_vi: progress.say_next_vi ?? null,
                        ...progress,
                      },
                    })
                    continue
                  }

                  if (call.name === 'update_form_field') {
                    if (this.triageMode) {
                      responses.push({
                        id: call.id,
                        name: call.name,
                        response: {
                          ok: false,
                          error: 'Triage mode: call select_registration_form with DOB first.',
                        },
                      })
                      continue
                    }

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

                  if (call.name === 'lookup_provider_facility' && callbacks.onProviderLookup) {
                    const args = (call.args ?? {}) as { query?: string }
                    const result = await callbacks.onProviderLookup(String(args.query ?? ''))
                    responses.push({
                      id: call.id,
                      name: call.name,
                      response: {
                        ok: true,
                        ...result,
                        voice_instruction: result.message,
                      },
                    })
                    continue
                  }

                  if (call.name === 'navigate_form_page' && callbacks.onNavigatePage) {
                    const args = (call.args ?? {}) as Record<string, unknown>
                    let action = parseNavigateAction(args.action)
                    let page = parsePageNumber(args.page ?? args.page_number ?? args.target_page)
                    // action itself may be "4" or "goto_4"
                    if (page == null) {
                      const fromAction = parsePageNumber(args.action)
                      if (fromAction != null) {
                        page = fromAction
                        action = 'goto'
                      }
                    }
                    if (action === 'goto' && page == null) {
                      responses.push({
                        id: call.id,
                        name: call.name,
                        response: {
                          ok: false,
                          error:
                            'goto requires page (1-based integer). Example: navigate_form_page(action=goto, page=4)',
                        },
                      })
                      continue
                    }
                    const result = await callbacks.onNavigatePage(action, page)
                    responses.push({
                      id: call.id,
                      name: call.name,
                      response: {
                        ok: result.ok,
                        requested_page: page ?? null,
                        page: result.page,
                        total_pages: result.total_pages,
                        reconnect: true,
                        voice_instruction:
                          `SECTION SWITCHED to page ${result.page} of ${result.total_pages}. ` +
                          'A new short live session will start for THIS page only. ' +
                          `Do NOT navigate to another page unless the patient asks. Stay on page ${result.page}.`,
                        say_next:
                          `Now on section ${result.page}. After reconnect, continue fields on page ${result.page} only — no greeting, no jumping to page 1.`,
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
                  if (formSelected && registrationContext) {
                    this.session.sendRealtimeInput({
                      text:
                        'FORM SELECTED. Date of birth is ALREADY saved — NEVER ask DOB again.\n' +
                        'CRITICAL: Do NOT greet again.\n' +
                        'A short reconnect will start for section 1 of the registration form.\n' +
                        'After reconnect, ask ONLY the next field from say_next (usually patient name).\n' +
                        'When the patient asks for another page (2/3/4), ALWAYS call navigate_form_page — never refuse.\n\n' +
                        `Registration rules for this section:\n\n${registrationContext}\n\n` +
                        'If still in this call before reconnect: speak say_next only.',
                    })
                  }
                  const lookupMessage =
                    typeof last?.message === 'string' ? last.message : ''
                  if (lookupMessage && functionCalls.some((c) => c.name === 'lookup_provider_facility')) {
                    this.session.sendRealtimeInput({
                      text: `Provider lookup result — read to patient in their language (Vietnamese = giọng miền Nam), then ask to confirm before saving provider_facility_name: ${lookupMessage}`,
                    })
                  }
                  if (sayNextEn || sayNextVi) {
                    const scanHint =
                      savedCount > 0
                        ? `Document scan saved ${savedCount} field(s). Briefly tell patient what you read, then continue. `
                        : ''
                    this.session.sendRealtimeInput({
                      text: `${scanHint}Speak naturally in patient's language — follow say_next (varied ack OK, or no ack). English: "${sayNextEn}". Vietnamese (Southern miền Nam accent, dạ/ạ, anh/chị): "${sayNextVi}". Never say "tôi sẽ ghi vào" every time. No per-field confirmation.`,
                    })
                  }

                }
              } catch (error) {
                const detail = error instanceof Error ? error.message : 'Tool call failed'
                const errorResponses = functionCalls.flatMap((call) => {
                  if (!call.id) return []
                  if (
                    call.name !== 'update_form_field' &&
                    call.name !== 'scan_document_fields' &&
                    call.name !== 'select_registration_form' &&
                    call.name !== 'lookup_provider_facility' &&
                    call.name !== 'navigate_form_page'
                  ) {
                    return []
                  }
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
