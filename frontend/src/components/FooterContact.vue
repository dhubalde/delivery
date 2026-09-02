<template>
  <div class="footer-contact" :class="{ 'is-contact': isContact }">
    <v-card
      density="compact"
      variant="tonal"
      rounded="lg"
      elevation="2"
      class="pa-2"
    >
      <div class="text-caption font-weight-medium d-flex align-center ga-1">
        <v-icon size="14">mdi-storefront</v-icon>
        <span>{{ merchantName }}</span>
      </div>
      <div class="text-caption d-flex align-center ga-1">
        <v-icon size="12">mdi-phone</v-icon>
        <span>{{ phone }}</span>
      </div>
      <div class="text-caption d-flex align-center ga-1">
        <v-icon size="12">mdi-email-outline</v-icon>
        <span>{{ email }}</span>
      </div>
      <div class="text-caption d-flex align-center ga-1">
        <v-icon size="12">mdi-map-marker-outline</v-icon>
        <span>{{ address }}</span>
      </div>
      <div v-if="hours" class="text-caption d-flex align-center ga-1">
        <v-icon size="12">mdi-clock-outline</v-icon>
        <span>{{ hours }}</span>
      </div>
      <v-divider class="my-2" />
      <div class="d-flex ga-1">
        <v-btn
          :href="socials.instagram"
          target="_blank"
          rel="noopener"
          icon="mdi-instagram"
          size="small"
          variant="text"
          density="comfortable"
          aria-label="Instagram"
        />
        <v-btn
          :href="socials.whatsapp"
          target="_blank"
          rel="noopener"
          icon="mdi-whatsapp"
          size="small"
          variant="text"
          density="comfortable"
          aria-label="WhatsApp"
        />
        <v-btn
          :href="socials.facebook"
          target="_blank"
          rel="noopener"
          icon="mdi-facebook"
          size="small"
          variant="text"
          density="comfortable"
          aria-label="Facebook"
        />
      </div>
    </v-card>
  </div>
</template>
<script setup lang="ts">
  import { computed } from "vue";
  import { useRoute } from "vue-router";
  import { useAuthStore } from "@/stores/auth.store";
  import { usePublicMerchant } from "@/composables/useMerchant";

  const route = useRoute();
  const isContact = computed(() => route.path.includes("/contact"));
  const auth = useAuthStore();
  const slug = computed(() => auth.merchantSlug || "ice-zone");
  const { data: merchantData } = usePublicMerchant(slug.value) as any;

  const m = computed(
    () => (merchantData.value ?? null) as Record<string, any> | null,
  );

  const merchantName = computed(() => "Group-q");
  const phone = computed(() => "3446-200156");
  const email = computed(() => "contacto@group-q.tech");
  const address = computed(() => (m.value?.address as string) || "—");
  const hours = computed(() => (m.value?.hours as string) || "");
  const socials = {
    instagram: "https://instagram.com/group-q.tech",
    whatsapp: "https://wa.me/543446200156",
    facebook: "https://facebook.com/group-q.tech",
  };
</script>
<style scoped>
  .footer-contact {
    position: fixed;
    bottom: 12px;
    right: 16px;
    z-index: 1006;
    width: 320px;
    max-width: calc(100vw - 24px);
    opacity: 0.98;
  }
  .footer-contact.is-contact {
    position: static;
    width: 100%;
    max-width: 600px;
    margin: 24px auto 0;
    transform: none;
  }
  @media (max-width: 960px) {
    .footer-contact {
      position: static;
      width: 100%;
      max-width: 100%;
      margin: 12px auto 0;
    }
    .footer-contact.is-contact {
      width: 100%;
      min-width: 0;
      max-width: 100%;
      margin: 0;
    }
  }
</style>
