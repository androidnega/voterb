/**
 * Serial upload queue — processes one file upload at a time with retries
 * to avoid parallel upload timeouts and server overload.
 */

const MAX_RETRIES = 2
const RETRY_DELAY_MS = 1500

class UploadQueue {
  constructor() {
    this.pending = []
    this.running = false
  }

  enqueue(taskFn, { label = 'upload' } = {}) {
    return new Promise((resolve, reject) => {
      this.pending.push({ taskFn, resolve, reject, label, attempt: 0 })
      this._drain()
    })
  }

  async _drain() {
    if (this.running) return
    this.running = true

    while (this.pending.length) {
      const job = this.pending.shift()
      try {
        const result = await job.taskFn()
        job.resolve(result)
      } catch (error) {
        if (job.attempt < MAX_RETRIES) {
          job.attempt += 1
          await sleep(RETRY_DELAY_MS * job.attempt)
          this.pending.unshift(job)
        } else {
          job.reject(error)
        }
      }
    }

    this.running = false
  }

  get size() {
    return this.pending.length + (this.running ? 1 : 0)
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export const uploadQueue = new UploadQueue()
