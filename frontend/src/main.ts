import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import { VueQueryPlugin, queryOptions } from './plugins/query'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(VueQueryPlugin, queryOptions)
app.mount('#app')
