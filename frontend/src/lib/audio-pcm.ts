export function downsampleTo16k(float32: Float32Array, inputSampleRate: number): Int16Array {
  if (inputSampleRate === 16000) {
    return floatToInt16(float32)
  }

  const ratio = inputSampleRate / 16000
  const newLength = Math.floor(float32.length / ratio)
  const result = new Int16Array(newLength)

  for (let i = 0; i < newLength; i++) {
    const idx = Math.floor(i * ratio)
    result[i] = floatToInt16Sample(float32[idx] ?? 0)
  }

  return result
}

function floatToInt16Sample(sample: number): number {
  const clamped = Math.max(-1, Math.min(1, sample))
  return clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff
}

function floatToInt16(float32: Float32Array): Int16Array {
  const result = new Int16Array(float32.length)
  for (let i = 0; i < float32.length; i++) {
    result[i] = floatToInt16Sample(float32[i])
  }
  return result
}

export function int16ToBase64(int16: Int16Array): string {
  const bytes = new Uint8Array(int16.buffer, int16.byteOffset, int16.byteLength)
  let binary = ''
  const chunk = 0x8000
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk))
  }
  return btoa(binary)
}

export function base64ToInt16(base64: string): Int16Array {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return new Int16Array(bytes.buffer)
}

export function int16ToFloat32(int16: Int16Array): Float32Array {
  const float32 = new Float32Array(int16.length)
  for (let i = 0; i < int16.length; i++) {
    float32[i] = int16[i] / 32768
  }
  return float32
}

export class PcmPlayer {
  private readonly context: AudioContext
  private nextStartTime = 0

  constructor(sampleRate = 24000) {
    this.context = new AudioContext({ sampleRate })
  }

  async resume() {
    if (this.context.state === 'suspended') {
      await this.context.resume()
    }
  }

  playBase64Pcm(base64: string) {
    const int16 = base64ToInt16(base64)
    const float32 = int16ToFloat32(int16)
    const buffer = this.context.createBuffer(1, float32.length, this.context.sampleRate)
    buffer.getChannelData(0).set(float32)

    const source = this.context.createBufferSource()
    source.buffer = buffer
    source.connect(this.context.destination)

    const now = this.context.currentTime
    const start = Math.max(now, this.nextStartTime)
    source.start(start)
    this.nextStartTime = start + buffer.duration
  }

  stop() {
    this.nextStartTime = 0
    void this.context.close()
  }

  getRemainingPlaybackMs(): number {
    return Math.max(0, (this.nextStartTime - this.context.currentTime) * 1000)
  }

  async waitForPlaybackDone(extraMs = 400): Promise<void> {
    const waitMs = this.getRemainingPlaybackMs() + extraMs
    if (waitMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, waitMs))
    }
  }
}

export class MicrophoneStreamer {
  private stream: MediaStream | null = null
  private audioContext: AudioContext | null = null
  private processor: ScriptProcessorNode | null = null
  private source: MediaStreamAudioSourceNode | null = null
  private active = false

  async start(onChunk: (base64Pcm: string) => void) {
    this.active = true

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    })

    this.audioContext = new AudioContext()
    await this.audioContext.resume()

    this.source = this.audioContext.createMediaStreamSource(this.stream)
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1)

    this.processor.onaudioprocess = (event) => {
      if (!this.active) return

      const input = event.inputBuffer.getChannelData(0)
      const pcm = downsampleTo16k(input, this.audioContext?.sampleRate ?? 48000)
      if (pcm.length > 0) {
        onChunk(int16ToBase64(pcm))
      }
    }

    this.source.connect(this.processor)
    this.processor.connect(this.audioContext.destination)
  }

  stop() {
    this.active = false

    if (this.processor) {
      this.processor.onaudioprocess = null
      this.processor.disconnect()
    }
    this.source?.disconnect()
    this.stream?.getTracks().forEach((track) => track.stop())
    void this.audioContext?.close()

    this.processor = null
    this.source = null
    this.stream = null
    this.audioContext = null
  }
}
