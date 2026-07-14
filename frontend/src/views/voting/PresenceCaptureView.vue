<template>
  <div class="presence-page">
    <button type="button" class="presence-back" @click="goBack">
      <i class="fas fa-arrow-left" aria-hidden="true"></i>
      Back
    </button>

    <FriendlyLoadState
      v-if="bootError"
      tone="error"
      title="Couldn’t open this step"
      :message="bootError"
      action-label="Try again"
      @action="boot"
    />

    <article v-else class="presence-card">
      <p class="presence-eyebrow">Quick photo</p>
      <h1 class="presence-title">Confirm it’s you</h1>
      <p class="presence-copy">
        Center your face, then tap the frame to take a photo.
      </p>

      <button
        type="button"
        class="presence-stage"
        :class="{ 'is-captured': !!previewUrl, 'is-live': !previewUrl && cameraReady }"
        :disabled="!!previewUrl || !cameraReady || uploading || cameraPending"
        aria-label="Take photo"
        @click="capture"
      >
        <video
          v-show="!previewUrl"
          ref="videoEl"
          class="presence-video"
          playsinline
          muted
          autoplay
        />
        <img
          v-if="previewUrl"
          :src="previewUrl"
          alt="Your photo preview"
          class="presence-preview"
        />
        <canvas ref="canvasEl" class="presence-canvas" hidden />

        <span v-if="!previewUrl && cameraReady" class="presence-guide" aria-hidden="true" />

        <div v-if="cameraPending" class="presence-overlay">
          <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
          <span>Starting camera…</span>
        </div>
        <div v-else-if="cameraError" class="presence-overlay presence-overlay--error">
          <i class="fas fa-exclamation-circle" aria-hidden="true"></i>
          <span>{{ cameraError }}</span>
          <a
            v-if="secureUpgradeUrl"
            class="presence-link"
            :href="secureUpgradeUrl"
            @click.stop
          >
            Open HTTPS version
          </a>
          <button type="button" class="presence-link" @click.stop="startCamera">
            Enable camera
          </button>
        </div>
        <div v-else-if="!previewUrl && !cameraReady" class="presence-overlay">
          <i class="fas fa-camera" aria-hidden="true"></i>
          <span>Tap to enable your camera</span>
          <button type="button" class="presence-link" @click.stop="startCamera">
            Enable camera
          </button>
        </div>
      </button>

      <p class="presence-note">
        <i class="fas fa-lock" aria-hidden="true"></i>
        Your photo is encrypted and kept secure.
      </p>

      <p v-if="uploadError" class="presence-error">{{ uploadError }}</p>

      <div v-if="previewUrl" class="presence-actions">
        <button
          type="button"
          class="presence-btn presence-btn--ghost"
          :disabled="uploading"
          @click="retake"
        >
          Retake
        </button>
        <button
          type="button"
          class="presence-btn presence-btn--primary"
          :disabled="uploading"
          @click="confirmAndContinue"
        >
          <i v-if="uploading" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
          <span>{{ uploading ? 'Saving…' : 'Continue' }}</span>
        </button>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { votingApi } from '@/api/voting'
import { friendlyActionError } from '@/utils/friendlyFeedback'
import FriendlyLoadState from '@/components/student/FriendlyLoadState.vue'

const route = useRoute()
const router = useRouter()
const electionUuid = route.params.uuid

const videoEl = ref(null)
const canvasEl = ref(null)
const bootError = ref('')
const cameraPending = ref(true)
const cameraReady = ref(false)
const cameraError = ref('')
const previewUrl = ref('')
const capturedBlob = ref(null)
const uploading = ref(false)
const uploadError = ref('')

let mediaStream = null

/** When on http://LAN-IP, offer https:// same path (camera requires secure context). */
const secureUpgradeUrl = computed(() => {
  if (typeof window === 'undefined' || window.isSecureContext) return ''
  try {
    const url = new URL(window.location.href)
    url.protocol = 'https:'
    return url.toString()
  } catch {
    return ''
  }
})

function goBack() {
  router.push(`/vote/${electionUuid}`)
}

function resolveGetUserMedia() {
  if (typeof navigator === 'undefined') return null

  // Ensure mediaDevices exists (some desktop browsers expose only legacy APIs)
  if (!navigator.mediaDevices) {
    try {
      navigator.mediaDevices = {}
    } catch {
      // read-only navigator in some environments
    }
  }

  if (typeof navigator.mediaDevices?.getUserMedia === 'function') {
    return (constraints) => navigator.mediaDevices.getUserMedia(constraints)
  }

  const legacy =
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia ||
    navigator.getUserMedia

  if (typeof legacy === 'function') {
    return (constraints) =>
      new Promise((resolve, reject) => {
        legacy.call(navigator, constraints, resolve, reject)
      })
  }

  return null
}

function cameraUnavailableMessage() {
  const insecure = typeof window !== 'undefined' && window.isSecureContext === false
  if (insecure) {
    return 'Browsers block the camera on plain HTTP when using an IP address. Open the HTTPS link (accept the certificate once), or use http://localhost on this machine.'
  }
  return 'Could not reach the camera API in this browser. Try Chrome or Edge, or check site camera permissions.'
}

function mapCameraError(err) {
  const name = err?.name || ''
  if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
    return 'Camera permission is required for the audit photo. Allow camera access, then tap Enable camera.'
  }
  if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
    return 'No camera was found. Plug in a webcam and tap Enable camera.'
  }
  if (name === 'NotReadableError' || name === 'TrackStartError') {
    return 'Camera is in use by another app. Close it and tap Enable camera.'
  }
  if (name === 'OverconstrainedError' || name === 'ConstraintNotSatisfiedError') {
    return 'This camera could not match the requested settings. Tap Enable camera.'
  }
  if (name === 'SecurityError') {
    return cameraUnavailableMessage()
  }
  return err?.message || 'Could not access your camera.'
}

async function requestCameraStream() {
  const getUserMedia = resolveGetUserMedia()
  if (!getUserMedia) {
    throw new Error(cameraUnavailableMessage())
  }

  // Soften constraints: strict facingMode/aspectRatio often fails on desktop webcams
  const attempts = [
    {
      audio: false,
      video: {
        facingMode: { ideal: 'user' },
        width: { ideal: 720 },
        height: { ideal: 720 },
      },
    },
    { audio: false, video: { facingMode: { ideal: 'user' } } },
    { audio: false, video: true },
  ]

  let lastError = null
  for (const constraints of attempts) {
    try {
      return await getUserMedia(constraints)
    } catch (err) {
      lastError = err
      const name = err?.name || ''
      if (
        name === 'NotAllowedError' ||
        name === 'PermissionDeniedError' ||
        name === 'SecurityError'
      ) {
        throw err
      }
    }
  }
  throw lastError || new Error('Could not access your camera.')
}

function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop())
    mediaStream = null
  }
  if (videoEl.value) {
    videoEl.value.srcObject = null
  }
  cameraReady.value = false
}

async function startCamera() {
  cameraError.value = ''
  cameraPending.value = true
  stopCamera()
  try {
    mediaStream = await requestCameraStream()
    await nextTick()
    const video = videoEl.value
    if (!video) {
      throw new Error('Camera preview failed to load. Tap Retry camera.')
    }
    video.srcObject = mediaStream
    video.muted = true
    video.setAttribute('playsinline', 'true')
    await video.play()
    cameraReady.value = true
  } catch (err) {
    console.error('Camera error:', err)
    cameraReady.value = false
    cameraError.value = mapCameraError(err)
  } finally {
    cameraPending.value = false
  }
}

function capture() {
  if (previewUrl.value || !cameraReady.value || uploading.value || cameraPending.value) return
  uploadError.value = ''
  const video = videoEl.value
  const canvas = canvasEl.value
  if (!video || !canvas) return

  const vw = video.videoWidth || 640
  const vh = video.videoHeight || 480
  const side = Math.min(vw, vh)
  const sx = Math.floor((vw - side) / 2)
  const sy = Math.floor((vh - side) / 2)

  canvas.width = side
  canvas.height = side
  const ctx = canvas.getContext('2d')
  ctx.translate(side, 0)
  ctx.scale(-1, 1)
  ctx.drawImage(video, sx, sy, side, side, 0, 0, side, side)

  canvas.toBlob((blob) => {
    if (!blob) {
      uploadError.value = 'Could not capture that frame. Please try again.'
      return
    }
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    capturedBlob.value = blob
    previewUrl.value = URL.createObjectURL(blob)
    stopCamera()
  }, 'image/jpeg', 0.88)
}

async function retake() {
  uploadError.value = ''
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  capturedBlob.value = null
  await startCamera()
}

async function confirmAndContinue() {
  if (!capturedBlob.value || uploading.value) return
  uploading.value = true
  uploadError.value = ''
  try {
    try {
      const { collectVoteAuditContext, cacheVoteAuditContext } = await import('@/utils/deviceAudit')
      const ctx = await collectVoteAuditContext({ includeLocation: true })
      cacheVoteAuditContext(electionUuid, ctx)
    } catch {
      /* non-blocking */
    }
    await votingApi.uploadPresence(electionUuid, capturedBlob.value, 'presence.jpg')
    // Confirm server recorded the selfie before opening the ballot
    const { data } = await votingApi.getPresence(electionUuid)
    if (!data?.presence_captured) {
      uploadError.value = 'Photo saved, but we couldn’t confirm it yet. Please try Confirm again.'
      return
    }
    await router.replace(`/vote/${electionUuid}/ballot`)
  } catch (err) {
    console.error('Presence upload failed:', err)
    if (err?.response?.data?.has_voted) {
      await router.replace(`/vote/${electionUuid}/confirmation`)
      return
    }
    uploadError.value = friendlyActionError(err, 'Could not save your photo. Please try again.')
  } finally {
    uploading.value = false
  }
}

async function boot() {
  bootError.value = ''
  try {
    const [eligibleRes, sessionRes] = await Promise.all([
      votingApi.getEligibleElections(),
      votingApi.getSvtSession(electionUuid),
    ])
    const elections = eligibleRes.data || []
    const match = elections.find((e) => String(e.uuid) === String(electionUuid))
    const session = sessionRes.data || {}

    if (match?.has_voted || session.status === 'voted' || session.has_voted) {
      await router.replace(`/vote/${electionUuid}/confirmation`)
      return
    }

    if (session.status !== 'validated') {
      await router.replace(`/vote/${electionUuid}`)
      return
    }

    if (session.presence_captured) {
      await router.replace(`/vote/${electionUuid}/ballot`)
      return
    }

    await startCamera()
  } catch (err) {
    console.error('Presence boot failed:', err)
    bootError.value = friendlyActionError(err, 'Something went wrong opening this step.')
  }
}

onMounted(boot)
onUnmounted(() => {
  stopCamera()
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>

<style scoped>
.presence-page {
  width: min(28rem, 100%);
  margin: 0 auto;
  padding: 0.5rem 0 2rem;
  display: grid;
  gap: 0.85rem;
}

.presence-back {
  border: none;
  background: transparent;
  color: #78716c;
  font-size: 0.8rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0;
  cursor: pointer;
  width: fit-content;
}

.presence-back:hover {
  color: #1c1917;
}

.presence-card {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1.25rem;
  padding: 1.15rem 1.1rem 1.2rem;
  display: grid;
  gap: 0.7rem;
  box-shadow: 0 4px 16px rgba(28, 25, 23, 0.03);
}

.presence-eyebrow {
  margin: 0;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0f766e;
}

.presence-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #1c1917;
  line-height: 1.2;
}

.presence-copy {
  margin: 0;
  font-size: 0.84rem;
  line-height: 1.5;
  color: #78716c;
}

.presence-stage {
  position: relative;
  margin: 0.35rem auto 0;
  width: min(100%, 18.5rem);
  aspect-ratio: 1 / 1;
  padding: 0;
  border-radius: 1.25rem;
  overflow: hidden;
  background: #1c1917;
  border: 1px solid #e7e5e4;
  box-shadow: 0 8px 24px rgba(28, 25, 23, 0.06);
  display: block;
  cursor: default;
  appearance: none;
  -webkit-appearance: none;
}

.presence-stage.is-live {
  cursor: pointer;
}

.presence-stage.is-live:hover {
  border-color: #d6d3d1;
}

.presence-stage.is-live:active {
  transform: scale(0.99);
}

.presence-stage:disabled {
  cursor: default;
}

.presence-stage.is-captured {
  border-color: #a7f3d0;
  box-shadow: 0 8px 24px rgba(15, 118, 110, 0.08);
}

.presence-video,
.presence-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
}

.presence-video {
  transform: scaleX(-1);
}

.presence-guide {
  position: absolute;
  inset: 12%;
  border-radius: 999px;
  border: 1.5px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 0 0 999px rgba(28, 25, 23, 0.22);
  pointer-events: none;
  z-index: 1;
}

.presence-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  gap: 0.55rem;
  justify-items: center;
  background: rgba(28, 25, 23, 0.72);
  color: #fafaf9;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 1rem;
  text-align: center;
}

.presence-overlay--error {
  color: #fecaca;
}

.presence-link {
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 0.74rem;
  font-weight: 650;
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.presence-note {
  margin: 0;
  display: flex;
  align-items: flex-start;
  gap: 0.45rem;
  font-size: 0.72rem;
  line-height: 1.45;
  color: #a8a29e;
}

.presence-note i {
  color: #0f766e;
  margin-top: 0.12rem;
}

.presence-error {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.45;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #f5e6d3;
  border-radius: 0.7rem;
  padding: 0.65rem 0.75rem;
}

.presence-actions {
  display: flex;
  gap: 0.55rem;
  justify-content: stretch;
  margin-top: 0.15rem;
}

.presence-btn {
  flex: 1;
  border: 1px solid #e7e5e4;
  background: #fff;
  color: #1c1917;
  font-size: 0.84rem;
  font-weight: 700;
  padding: 0.78rem 1rem;
  border-radius: 0.9rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
}

.presence-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.presence-btn--primary {
  background: #1c1917;
  border-color: #1c1917;
  color: #fff;
}

.presence-btn--ghost {
  background: #fff;
}

@media (min-width: 768px) {
  .presence-card {
    padding: 1.35rem 1.3rem 1.35rem;
  }

  .presence-title {
    font-size: 1.25rem;
  }
}
</style>
