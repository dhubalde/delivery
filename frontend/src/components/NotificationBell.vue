<template>
  <div class="notification-bell">
    <v-menu
      v-model="showDropdown"
      anchor="bottom end"
      location="bottom end"
      :close-on-content-click="false"
    >
      <template #activator="{ props: menuProps }">
        <div v-bind="menuProps" class="bell-activator">
          <v-badge
            :content="unreadCount"
            :model-value="unreadCount > 0"
            color="grey-darken-1"
            location="top end"
            offset-x="4"
            offset-y="9"
            :max="99"
            class="bell-badge"
          >
            <v-btn
              icon="mdi-bell-outline"
              variant="text"
              aria-label="Notificaciones"
            />
          </v-badge>
        </div>
      </template>

      <v-card min-width="340" max-height="420" elevation="12" rounded="lg">
        <v-card-title class="d-flex align-center pa-3">
          <span class="text-subtitle-1 font-weight-bold">Notificaciones</span>
          <v-spacer />
          <v-btn
            density="compact"
            variant="text"
            color="primary"
            :disabled="unreadCount === 0"
            @click="handleMarkAllRead"
          >
            Marcar todas como leídas
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-list density="compact" class="notify-list pa-2">
          <template v-if="filteredNotifications.length === 0">
            <v-list-item disabled rounded="lg">
              <div class="text-center text-medium-emphasis pa-4">Sin notificaciones</div>
            </v-list-item>
          </template>
          <template v-else>
            <v-list-item
              v-for="notif in filteredNotifications"
              :key="notif.id"
              :variant="notif.is_read ? 'plain' : 'tonal'"
              :color="notif.is_read ? '' : 'grey-lighten-4'"
              class="notify-item mb-2"
              :class="{ 'notify-item--unread': !notif.is_read }"
              rounded="lg"
              @click="openNotification(notif)"
            >
              <v-list-item-subtitle class="text-caption text-medium-emphasis">
                {{ formatDate(notif.created_at) }}
              </v-list-item-subtitle>
              <v-list-item-title class="text-body-2 text-wrap">
                {{ notif.message }}
              </v-list-item-title>
              <v-list-item-subtitle v-if="notif.recipient_name" class="text-caption">
                {{ notif.recipient_name }}
              </v-list-item-subtitle>
              <template #append>
                <v-btn
                  icon="mdi-close"
                  size="x-small"
                  variant="text"
                  color="grey-darken-1"
                  class="ml-2 delete-btn"
                  @click.stop="handleDelete(notif.id)"
                />
              </template>
            </v-list-item>
          </template>
        </v-list>
      </v-card>
    </v-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotifications } from '@/composables/useNotifications'
import { getMyOrderIds } from '@/composables/useMyOrders'

const props = withDefaults(defineProps<{ recipientType?: 'CUSTOMER' | 'EMPLOYEE' | null }>(), {
  recipientType: null,
})

const { notifications: allNotifications, markRead, markAllRead, remove } = useNotifications(
  props.recipientType ? { recipientType: props.recipientType } : undefined,
)
const showDropdown = ref(false)
const router = useRouter()
const route = useRoute()

// — Filtro por cliente: en catálogo solo las notificaciones de SUS pedidos (localStorage myOrders)
const myIds = ref<number[]>(getMyOrderIds())
function refreshMyIds() {
  myIds.value = getMyOrderIds()
}
onMounted(() => {
  window.addEventListener('myOrders:updated', refreshMyIds as EventListener)
  window.addEventListener('storage', (e: StorageEvent) => {
    if (e.key === 'myOrders') refreshMyIds()
  })
})
onUnmounted(() => {
  window.removeEventListener('myOrders:updated', refreshMyIds as EventListener)
})

const filteredNotifications = computed(() => {
  const all = allNotifications.value ?? []
  if (props.recipientType !== 'CUSTOMER') return all
  if (myIds.value.length === 0) return []
  const set = new Set(myIds.value)
  // Customer policy (LOGISTICA-only): hide historic RECIBIDO/PREPARACION rows
  // already in DB; keep only "en camino" (logistics) notifications.
  const isLogistics = (n: { message?: string; state?: string; order_state?: string }) => {
    const state = n.state ?? n.order_state ?? ''
    if (typeof state === 'string' && state.toUpperCase() === 'LOGISTICA') return true
    return /en camino/i.test(n.message ?? '')
  }
  // solo notificaciones cuyo order esté en mis pedidos
  return all.filter((n) => n.order !== null && set.has(n.order) && isLogistics(n))
})

const unreadCount = computed(() => filteredNotifications.value.filter((n) => !n.is_read).length)

const handleMarkRead = async (id: number) => {
  await markRead.mutateAsync(id)
}

type NotificationRow = { id: number; order: number | null }

/**
 * Opening a notification marks it read and, when it points at an order, takes
 * you to that order: the board (employee) or my orders (customer). A deep link
 * without a target only marks it read.
 */
async function openNotification(notif: NotificationRow) {
  try {
    await handleMarkRead(notif.id)
  } catch {
    // the mutation already reports its own error toast
  }
  if (notif.order == null) return
  showDropdown.value = false
  if (props.recipientType === 'CUSTOMER') {
    const slug = (route.params.slug as string) || 'ice-zone'
    router.push({ name: 'my-orders', params: { slug }, query: { order: String(notif.order) } })
  } else {
    router.push({ path: '/panel/board', query: { order: String(notif.order) } })
  }
}

const handleMarkAllRead = async () => {
  await markAllRead.mutateAsync()
  window.dispatchEvent(
    new CustomEvent('app:toast', { detail: { msg: 'Todas las notificaciones marcadas como leídas', type: 'success' } })
  )
}

const handleDelete = async (id: number) => {
  try {
    await remove.mutateAsync(id)
    window.dispatchEvent(
      new CustomEvent('app:toast', { detail: { msg: 'Notificación eliminada', type: 'success' } })
    )
  } catch {
    // el toast de error ya lo dispara onError en useNotifications
  }
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    if (diffMin < 1) return 'Hace un momento'
    if (diffMin < 60) return `Hace ${diffMin} min`
    const diffH = Math.floor(diffMin / 60)
    if (diffH < 24) return `Hace ${diffH}h`
    return d.toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })
  } catch {
    return iso
  }
}
</script>

<style scoped>
.notification-bell {
  position: relative;
  overflow: visible;
}
.bell-activator {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}
.bell-badge {
  overflow: visible;
}
/* The count bubble sits above the button; without this it swallows the click
   and the dropdown never opens when you aim at the badge. */
.bell-badge :deep(.v-badge__badge) {
  font-size: 11px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  transform: translate(2px, 1px);
  pointer-events: none;
}
.notify-list {
  background: transparent;
}
.notify-item {
  cursor: pointer;
  transition: background-color 0.15s ease;
  border-radius: 12px !important;
  border: 1px solid rgba(0, 0, 0, 0.06);
}
.notify-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}
.notify-item--unread {
  background-color: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.08);
}
.notify-item--unread:hover {
  background-color: rgba(0, 0, 0, 0.08);
}
.delete-btn {
  opacity: 0.6;
  transition: opacity 0.15s;
}
.delete-btn:hover {
  opacity: 1;
}
</style>
