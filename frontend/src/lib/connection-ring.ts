/** Phone-style ring tone while waiting for Gemini Live to connect. */
export class ConnectionRingtone {
  private audioCtx: AudioContext | null = null
  private intervalId: ReturnType<typeof setInterval> | null = null
  private stopped = true

  async start(): Promise<void> {
    await this.stop()
    this.stopped = false
    this.audioCtx = new AudioContext()
    await this.audioCtx.resume()
    this.playRingCycle()
    this.intervalId = setInterval(() => this.playRingCycle(), 4000)
  }

  async stop(): Promise<void> {
    this.stopped = true
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
    if (this.audioCtx) {
      await this.audioCtx.close().catch(() => undefined)
      this.audioCtx = null
    }
  }

  private playRingCycle(): void {
    if (this.stopped || !this.audioCtx) return

    const ctx = this.audioCtx
    const now = ctx.currentTime

    for (const freq of [440, 480]) {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.frequency.value = freq
      osc.type = 'sine'
      gain.gain.setValueAtTime(0, now)
      gain.gain.linearRampToValueAtTime(0.12, now + 0.05)
      gain.gain.setValueAtTime(0.12, now + 1.8)
      gain.gain.linearRampToValueAtTime(0, now + 2)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(now)
      osc.stop(now + 2)
    }
  }
}
