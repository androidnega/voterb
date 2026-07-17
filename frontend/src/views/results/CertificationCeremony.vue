<template>
  <div class="admin-page ceremony">
    <div class="ceremony__top">
      <button type="button" class="btn btn-ghost" @click="goBack">
        <i class="fas fa-arrow-left"></i>
        Back to results
      </button>
      <div>
        <h1 class="ceremony__title">Certify results</h1>
        <p class="ceremony__sub">
          {{ electionTitle || 'Election results' }} — capture photo, location, and signature to certify.
        </p>
      </div>
    </div>

    <ol class="ceremony-steps">
      <li
        v-for="s in steps"
        :key="s.id"
        class="ceremony-steps__item"
        :class="{
          'is-active': step === s.id,
          'is-done': step > s.id,
        }"
      >
        <span class="ceremony-steps__num">{{ s.id }}</span>
        <span>{{ s.label }}</span>
      </li>
    </ol>

    <!-- Step 1: Photo -->
    <section v-if="step === 1" class="ceremony-panel">
      <h2>Capture certifier photo</h2>
      <p class="ceremony-panel__hint">Use your webcam to take a photo for the certification record.</p>

      <div class="photo-stage">
        <video v-show="!photoDataUrl" ref="videoEl" class="photo-stage__media" autoplay playsinline muted />
        <img v-if="photoDataUrl" :src="photoDataUrl" alt="Captured photo" class="photo-stage__media" />
        <canvas ref="photoCanvasEl" hidden />
      </div>

      <p v-if="cameraError" class="ceremony-error">{{ cameraError }}</p>

      <div class="ceremony-actions">
        <button v-if="!photoDataUrl" type="button" class="btn btn-primary" :disabled="startingCamera" @click="startCamera">
          <i v-if="startingCamera" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-video"></i>
          {{ stream ? 'Retake setup' : 'Start camera' }}
        </button>
        <button v-if="stream && !photoDataUrl" type="button" class="btn btn-primary" @click="capturePhoto">
          <i class="fas fa-camera"></i>
          Capture
        </button>
        <button v-if="photoDataUrl" type="button" class="btn btn-ghost" @click="retakePhoto">
          Retake
        </button>
        <button type="button" class="btn btn-primary" :disabled="!photoDataUrl" @click="step = 2">
          Continue
        </button>
      </div>
    </section>

    <!-- Step 2: Location -->
    <section v-else-if="step === 2" class="ceremony-panel">
      <h2>Confirm location</h2>
      <p class="ceremony-panel__hint">Allow GPS access, or enter coordinates manually if GPS is unavailable.</p>

      <div v-if="location" class="location-card">
        <p><strong>Latitude:</strong> {{ location.lat }}</p>
        <p><strong>Longitude:</strong> {{ location.lng }}</p>
        <p v-if="location.accuracy != null" class="text-muted">Accuracy ±{{ Math.round(location.accuracy) }}m</p>
        <p class="text-muted">Source: {{ location.source }}</p>
      </div>

      <p v-if="locationError" class="ceremony-error">{{ locationError }}</p>

      <div class="manual-location">
        <label>Manual latitude</label>
        <InputText v-model="manualLat" class="w-full" placeholder="e.g. 6.6885" />
        <label>Manual longitude</label>
        <InputText v-model="manualLng" class="w-full" placeholder="e.g. -1.6244" />
      </div>

      <div class="ceremony-actions">
        <button type="button" class="btn btn-ghost" @click="step = 1">Back</button>
        <button type="button" class="btn btn-ghost" :disabled="locating" @click="captureGps">
          <i v-if="locating" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-map-marker-alt"></i>
          Use GPS
        </button>
        <button type="button" class="btn btn-ghost" @click="applyManualLocation">Use manual</button>
        <button type="button" class="btn btn-primary" :disabled="!location" @click="goToSignature">
          Continue
        </button>
      </div>
    </section>

    <!-- Step 3: Signature -->
    <section v-else-if="step === 3" class="ceremony-panel">
      <h2>Draw signature</h2>
      <p class="ceremony-panel__hint">Sign in the box below using your mouse or finger.</p>

      <canvas
        ref="sigCanvasEl"
        class="sig-canvas"
        width="640"
        height="220"
        @pointerdown="onSigPointerDown"
        @pointermove="onSigPointerMove"
        @pointerup="onSigPointerUp"
        @pointerleave="onSigPointerUp"
      />

      <div class="ceremony-actions">
        <button type="button" class="btn btn-ghost" @click="step = 2">Back</button>
        <button type="button" class="btn btn-ghost" @click="clearSignature">Clear</button>
        <button type="button" class="btn btn-primary" :disabled="!hasSignature" @click="goToConfirm">
          Continue
        </button>
      </div>
    </section>

    <!-- Step 4: Confirm -->
    <section v-else class="ceremony-panel">
      <h2>Confirm &amp; certify</h2>
      <p class="ceremony-panel__hint">Review the evidence. IP and device fingerprint are recorded automatically.</p>

      <div class="confirm-grid">
        <div class="confirm-card">
          <h3>Photo</h3>
          <img v-if="photoDataUrl" :src="photoDataUrl" alt="Certifier photo" class="confirm-photo" />
        </div>
        <div class="confirm-card">
          <h3>Location</h3>
          <p v-if="location">{{ location.lat }}, {{ location.lng }}</p>
          <p class="text-muted">{{ location?.source }}</p>
        </div>
        <div class="confirm-card">
          <h3>Signature</h3>
          <img v-if="signatureDataUrl" :src="signatureDataUrl" alt="Signature" class="confirm-sig" />
        </div>
        <div class="confirm-card">
          <h3>Device</h3>
          <p><strong>IP:</strong> {{ clientIp || '…' }}</p>
          <p class="mono fingerprint"><strong>Fingerprint:</strong> {{ fingerprint }}</p>
        </div>
      </div>

      <p v-if="submitError" class="ceremony-error">{{ submitError }}</p>

      <div class="ceremony-actions">
        <button type="button" class="btn btn-ghost" :disabled="submitting" @click="step = 3">Back</button>
        <button type="button" class="btn btn-primary" :disabled="submitting || !canSubmit" @click="submitCertification">
          <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-stamp"></i>
          {{ submitting ? 'Certifying…' : 'Certify results' }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import { resultsApi } from '@/api/results'
import { collectVoteAuditContext } from '@/utils/deviceAudit'
import { usePageHeading } from '@/composables/usePageHeading'

const route = useRoute()
const router = useRouter()
const { setPageHeading } = usePageHeading()
setPageHeading({
  title: 'Certification ceremony',
  subtitle: 'Photo, location, and signature required to certify results.',
})

const steps = [
  { id: 1, label: 'Photo' },
  { id: 2, label: 'Location' },
  { id: 3, label: 'Signature' },
  { id: 4, label: 'Confirm' },
]

const step = ref(1)
const electionTitle = ref('')
const photoDataUrl = ref('')
const signatureDataUrl = ref('')
const location = ref(null)
const manualLat = ref('')
const manualLng = ref('')
const fingerprint = ref('')
const clientIp = ref('')
const cameraError = ref('')
const locationError = ref('')
const submitError = ref('')
const startingCamera = ref(false)
const locating = ref(false)
const submitting = ref(false)
const hasSignature = ref(false)

const videoEl = ref(null)
const photoCanvasEl = ref(null)
const sigCanvasEl = ref(null)
const stream = ref(null)
let drawing = false
let lastPoint = null

const canSubmit = computed(() =>
  Boolean(photoDataUrl.value && location.value && signatureDataUrl.value && fingerprint.value)
)

const goBack = () => router.push(`/results/${route.params.uuid}`)

const stopCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach((t) => t.stop())
    stream.value = null
  }
}

const startCamera = async () => {
  cameraError.value = ''
  startingCamera.value = true
  stopCamera()
  try {
    const media = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    })
    stream.value = media
    await nextTick()
    if (videoEl.value) {
      videoEl.value.srcObject = media
      await videoEl.value.play()
    }
  } catch (err) {
    cameraError.value = err?.message || 'Unable to access camera. Check browser permissions.'
  } finally {
    startingCamera.value = false
  }
}

const capturePhoto = () => {
  const video = videoEl.value
  const canvas = photoCanvasEl.value
  if (!video || !canvas) return
  const w = video.videoWidth || 640
  const h = video.videoHeight || 480
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0, w, h)
  photoDataUrl.value = canvas.toDataURL('image/jpeg', 0.85)
  stopCamera()
}

const retakePhoto = async () => {
  photoDataUrl.value = ''
  await startCamera()
}

const captureGps = () => {
  locationError.value = ''
  locating.value = true
  if (!navigator.geolocation) {
    locationError.value = 'Geolocation is not available. Enter coordinates manually.'
    locating.value = false
    return
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      location.value = {
        lat: Number(pos.coords.latitude.toFixed(6)),
        lng: Number(pos.coords.longitude.toFixed(6)),
        accuracy: pos.coords.accuracy,
        source: 'gps',
      }
      locating.value = false
    },
    (err) => {
      locationError.value = err?.message || 'GPS failed. Enter coordinates manually.'
      locating.value = false
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
  )
}

const applyManualLocation = () => {
  const lat = Number(manualLat.value)
  const lng = Number(manualLng.value)
  if (Number.isNaN(lat) || Number.isNaN(lng)) {
    locationError.value = 'Enter valid numeric latitude and longitude.'
    return
  }
  if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
    locationError.value = 'Latitude must be -90…90 and longitude -180…180.'
    return
  }
  locationError.value = ''
  location.value = { lat, lng, accuracy: null, source: 'manual' }
}

const initSigCanvas = () => {
  const canvas = sigCanvasEl.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.strokeStyle = '#0f172a'
  ctx.lineWidth = 2.5
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  hasSignature.value = false
  signatureDataUrl.value = ''
}

const pointerPos = (e) => {
  const canvas = sigCanvasEl.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY,
  }
}

const onSigPointerDown = (e) => {
  drawing = true
  lastPoint = pointerPos(e)
  sigCanvasEl.value?.setPointerCapture?.(e.pointerId)
}

const onSigPointerMove = (e) => {
  if (!drawing || !sigCanvasEl.value) return
  const ctx = sigCanvasEl.value.getContext('2d')
  const point = pointerPos(e)
  ctx.beginPath()
  ctx.moveTo(lastPoint.x, lastPoint.y)
  ctx.lineTo(point.x, point.y)
  ctx.stroke()
  lastPoint = point
  hasSignature.value = true
}

const onSigPointerUp = () => {
  drawing = false
  lastPoint = null
}

const clearSignature = () => initSigCanvas()

const goToSignature = async () => {
  step.value = 3
  await nextTick()
  initSigCanvas()
}

const goToConfirm = async () => {
  if (!hasSignature.value || !sigCanvasEl.value) return
  signatureDataUrl.value = sigCanvasEl.value.toDataURL('image/png')
  step.value = 4
  try {
    const { data } = await resultsApi.certifyMeta(route.params.uuid, fingerprint.value)
    clientIp.value = data.ip_address || 'Unavailable'
  } catch {
    clientIp.value = 'Captured on submit'
  }
}

const submitCertification = async () => {
  submitError.value = ''
  submitting.value = true
  try {
    await resultsApi.certify(route.params.uuid, {
      certification_evidence: {
        photo: photoDataUrl.value,
        location: {
          lat: location.value.lat,
          lng: location.value.lng,
          accuracy: location.value.accuracy,
          source: location.value.source,
        },
        signature: signatureDataUrl.value,
        device_fingerprint: fingerprint.value,
      },
    }, fingerprint.value)
    router.push(`/results/${route.params.uuid}`)
  } catch (err) {
    submitError.value =
      err?.response?.data?.error
      || err?.response?.data?.detail
      || 'Certification failed. Please try again.'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await resultsApi.preview(route.params.uuid)
    electionTitle.value = data?.election?.title || ''
    if (!['generated', 'pending_certification'].includes(data?.status)) {
      router.replace(`/results/${route.params.uuid}`)
      return
    }
  } catch {
    router.replace('/results')
    return
  }

  const ctx = await collectVoteAuditContext({ includeLocation: false })
  fingerprint.value = ctx.fingerprint || ''
  await startCamera()
})

onBeforeUnmount(() => {
  stopCamera()
})
</script>

<style scoped>
.ceremony__top {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.ceremony__title {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--vb-ink, #1c1c1c);
}

.ceremony__sub {
  margin: 0.3rem 0 0;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.9rem;
  line-height: 1.45;
  max-width: 40rem;
}

.ceremony-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  list-style: none;
  padding: 0.3rem;
  margin: 0 0 1.25rem;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 999px;
  width: fit-content;
  max-width: 100%;
}

.ceremony-steps__item {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  background: transparent;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.78rem;
  font-weight: 700;
  transition: all 0.16s ease;
}

.ceremony-steps__item.is-active {
  background: var(--vb-accent, #3d4f44);
  color: #fff;
  box-shadow: 0 6px 16px var(--vb-accent-shadow, rgba(61, 79, 68, 0.18));
}

.ceremony-steps__item.is-done {
  background: var(--vb-accent-soft, #e8efe6);
  color: var(--vb-accent, #3d4f44);
}

.ceremony-steps__num {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  background: rgba(28, 28, 28, 0.06);
  font-size: 0.68rem;
}

.ceremony-steps__item.is-active .ceremony-steps__num {
  background: rgba(255, 255, 255, 0.2);
}

.ceremony-panel {
  background: #fff;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: var(--vb-card-radius, 1.25rem);
  padding: 1.25rem 1.35rem;
  box-shadow: var(--vb-card-shadow, 0 8px 28px rgba(28, 28, 28, 0.05));
  animation: pane-in 0.22s ease;
}

.ceremony-panel h2 {
  margin: 0 0 0.35rem;
  font-size: 1.08rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.ceremony-panel__hint {
  margin: 0 0 1rem;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.86rem;
  line-height: 1.45;
}

.photo-stage {
  max-width: 420px;
  aspect-ratio: 4 / 3;
  background: #1c1c1c;
  border-radius: 1rem;
  overflow: hidden;
  margin-bottom: 1rem;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
}

.photo-stage__media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ceremony-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
}

.ceremony-error {
  color: #be123c;
  font-size: 0.875rem;
  margin: 0.5rem 0;
}

.location-card {
  display: grid;
  gap: 0.35rem;
  margin-bottom: 1rem;
  max-width: 360px;
  padding: 0.85rem 0.95rem;
  border-radius: 0.9rem;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
}

.manual-location {
  display: grid;
  gap: 0.45rem;
  margin-bottom: 1rem;
  max-width: 360px;
}

.manual-location label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--vb-ink, #1c1c1c);
}

.sig-canvas {
  width: 100%;
  max-width: 640px;
  height: auto;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.9rem;
  touch-action: none;
  cursor: crosshair;
  background: #fff;
}

.confirm-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
}

@media (min-width: 800px) {
  .confirm-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.confirm-card {
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 1rem;
  padding: 0.9rem;
  background: var(--vb-panel, #f7f6f2);
}

.confirm-card h3 {
  margin: 0 0 0.5rem;
  font-size: 0.78rem;
  font-weight: 750;
  color: var(--vb-muted, #8a8a8a);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.confirm-photo,
.confirm-sig {
  max-width: 100%;
  border-radius: 0.75rem;
  background: #fff;
}

.fingerprint {
  word-break: break-all;
  font-size: 0.75rem;
}

.text-muted {
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.85rem;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

@keyframes pane-in {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
</style>
