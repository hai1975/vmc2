const MAX_SIZE = 768
const JPEG_QUALITY = 0.72
const FRAME_INTERVAL_MS = 1000

export class VideoFrameStreamer {
  private stream: MediaStream | null = null
  private timer: ReturnType<typeof setInterval> | null = null
  private videoEl: HTMLVideoElement | null = null
  private canvas: HTMLCanvasElement | null = null

  getStream(): MediaStream | null {
    return this.stream
  }

  async start(videoEl: HTMLVideoElement, onFrame: (base64Jpeg: string) => void): Promise<void> {
    await this.stop()
    this.videoEl = videoEl

    const constraints: MediaStreamConstraints[] = [
      {
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      },
      { video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
      { video: true, audio: false },
    ]

    let lastError: unknown = null
    for (const constraint of constraints) {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia(constraint)
        break
      } catch (error) {
        lastError = error
      }
    }

    if (!this.stream) {
      throw lastError instanceof Error ? lastError : new Error('Could not open webcam')
    }

    videoEl.srcObject = this.stream
    await videoEl.play()

    this.timer = setInterval(() => {
      const frame = this.captureFrame()
      if (frame) onFrame(frame)
    }, FRAME_INTERVAL_MS)

    const first = this.captureFrame()
    if (first) onFrame(first)
  }

  captureFrame(): string | null {
    const video = this.videoEl
    if (!video || !video.videoWidth) return null

    if (!this.canvas) {
      this.canvas = document.createElement('canvas')
    }

    const srcW = video.videoWidth
    const srcH = video.videoHeight
    const scale = Math.min(1, MAX_SIZE / Math.max(srcW, srcH))
    const w = Math.round(srcW * scale)
    const h = Math.round(srcH * scale)

    this.canvas.width = w
    this.canvas.height = h
    const ctx = this.canvas.getContext('2d')
    if (!ctx) return null

    ctx.drawImage(video, 0, 0, w, h)
    const dataUrl = this.canvas.toDataURL('image/jpeg', JPEG_QUALITY)
    const comma = dataUrl.indexOf(',')
    return comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl
  }

  async stop(): Promise<void> {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
    }
    this.stream?.getTracks().forEach((t) => t.stop())
    this.stream = null
    if (this.videoEl) {
      this.videoEl.srcObject = null
    }
    this.videoEl = null
  }
}
