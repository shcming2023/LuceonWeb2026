<script setup lang="ts">
import { Document, EditPen, Files, HomeFilled, Setting, SwitchButton, User, View } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { ref, computed } from 'vue'
import { logoutUser, useCurrentUser } from '@/utils/user'

const router = useRouter()
const route = useRoute()

const menuItems = [
  { icon: HomeFilled, path: '/', tooltip: '首页', label: '首页' },
  { icon: Document, path: '/files', tooltip: '文件管理', label: '文件' },
  { icon: View, path: '/review/pdf', tooltip: 'PDF解析审查', label: 'PDF审查' },
  { icon: Files, path: '/review/outline', tooltip: '目录重建审查', label: '目录审查' },
  { icon: View, path: '/review/standard', tooltip: '标准输出物审查', label: '标准审查' },
  { icon: EditPen, path: '/review/final', tooltip: 'Standard质量验收', label: '质检' },
  { icon: Setting, path: '/settings', tooltip: '运行设置', label: '设置' }
]

const activeMenu = computed(() => {
  const path = route.path
  if (path === '/') return '/'
  if (path.startsWith('/review/preview')) {
    return route.query.outline === '1' ? '/review/outline' : '/review/pdf'
  }
  if (path.startsWith('/review/final')) return '/review/final'
  if (path.startsWith('/review/standard')) return '/review/standard'
  if (path.startsWith('/review/outline')) return '/review/outline'
  if (path.startsWith('/review/pdf') || path === '/review') return '/review/pdf'
  if (path.startsWith('/settings')) return '/settings'
  if (path.startsWith('/files')) return '/files'
  return menuItems.find(item => path === item.path)?.path || path
})

const isAuthPage = computed(() => route.meta.public === true)
const currentUser = useCurrentUser()

const sidebarHover = ref(false)

const handleLogout = async () => {
  try {
    await logoutUser()
  } finally {
    router.push('/login')
  }
}
</script>

<template>
  <router-view v-if="isAuthPage" />
  <div v-else class="mineru-layout">
    <!-- 侧边栏 -->
    <aside 
      class="sidebar" 
      :class="{ 'sidebar-expanded': sidebarHover }"
      @mouseenter="sidebarHover = true"
      @mouseleave="sidebarHover = false"
    >
      <div class="logo-area">
        <div class="logo-wrapper">
          <img src="/logo.png" alt="logo" class="logo" />
          <transition name="fade">
            <span v-show="sidebarHover" class="logo-text">Luceon</span>
          </transition>
        </div>
      </div>
      
      <nav class="nav-menu">
        <div 
          v-for="item in menuItems" 
          :key="item.path" 
          class="nav-item" 
          :class="{ active: activeMenu === item.path }" 
          @click="router.push(item.path)"
        >
          <div class="nav-icon-wrapper">
            <el-icon :size="22"><component :is="item.icon" /></el-icon>
          </div>
          <transition name="fade">
            <span v-show="sidebarHover" class="nav-label">{{ item.label }}</span>
          </transition>
          <div v-if="activeMenu === item.path" class="nav-indicator"></div>
        </div>
      </nav>
      
      <div class="sidebar-bottom">
        <div class="user-item">
          <div class="nav-icon-wrapper">
            <el-icon :size="20"><User /></el-icon>
          </div>
          <transition name="fade">
            <span v-show="sidebarHover" class="user-email">{{ currentUser?.email }}</span>
          </transition>
        </div>

        <div class="nav-item logout-item" @click="handleLogout">
          <div class="nav-icon-wrapper">
            <el-icon :size="20"><SwitchButton /></el-icon>
          </div>
          <transition name="fade">
            <span v-show="sidebarHover" class="nav-label">退出</span>
          </transition>
        </div>
        
        <div class="version-badge">
          <span class="version-dot"></span>
          <transition name="fade">
            <span v-show="sidebarHover" class="version-text">2026</span>
          </transition>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-area">
      <template v-if="route.name === 'FilePreview' || route.name === 'ReviewPreview'">
        <router-view />
      </template>
      <template v-else>
        <main class="content-area">
          <div :class="['content-wrapper', { 'content-full': route.path !== '/' }]">
            <router-view />
          </div>
        </main>
      </template>
    </div>
  </div>
</template>

<style scoped>
.mineru-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-secondary);
}

/* 侧边栏 */
.sidebar {
  width: 72px;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: var(--shadow-md);
  z-index: 100;
  padding: 16px 12px;
  flex-shrink: 0;
  min-height: 100vh;
  transition: width var(--transition-normal);
  position: relative;
}

.sidebar-expanded {
  width: 180px;
}

/* Logo区域 */
.logo-area {
  padding: 8px 0 24px;
  width: 100%;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.logo {
  width: 36px;
  height: 36px;
  transition: transform var(--transition-normal);
}

.sidebar:hover .logo {
  transform: scale(1.05);
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  white-space: nowrap;
}

/* 导航菜单 */
.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  padding: 0 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  color: var(--text-muted);
  gap: 12px;
}

.nav-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--primary-tint);
  color: var(--primary-color);
}

.nav-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--primary-gradient);
  border-radius: 0 3px 3px 0;
}

/* 底部区域 */
.sidebar-bottom {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  padding: 0 4px;
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}

.settings-item {
  margin-bottom: 4px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  color: var(--text-secondary);
  overflow: hidden;
}

.user-email {
  min-width: 0;
  max-width: 104px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 500;
}

.github-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  transition: all var(--transition-normal);
}

.github-link:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.github-link img {
  opacity: 0.6;
  transition: opacity var(--transition-normal);
}

.github-link:hover img {
  opacity: 1;
}

.logout-item {
  color: var(--text-muted);
}

.logout-item:hover {
  color: var(--danger-color);
}

.version-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 12px;
}

.version-dot {
  width: 8px;
  height: 8px;
  background: var(--success-color);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.version-text {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}

/* 主内容区 */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
}

.content-area {
  flex: 1;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: stretch;
  padding: 24px;
  min-height: 0;
}

.content-wrapper {
  width: 100%;
  max-width: 1200px;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: 24px;
  animation: fadeIn 0.3s ease;
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.content-full {
  max-width: none;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
  height: 100%;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 1200px) {
  .content-area {
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .mineru-layout {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    min-height: auto;
    padding: 12px 16px;
    flex-direction: row;
    align-items: center;
    gap: 8px;
  }
  
  .sidebar-expanded {
    width: 100%;
  }
  
  .logo-area {
    padding: 0;
    width: auto;
  }
  
  .logo-text {
    display: none;
  }
  
  .nav-menu {
    flex-direction: row;
    flex: 1;
    justify-content: center;
    gap: 4px;
    padding: 0;
  }
  
  .nav-item {
    padding: 10px 14px;
  }
  
  .nav-label {
    display: none;
  }
  
  .nav-indicator {
    display: none;
  }
  
  .sidebar-bottom {
    flex-direction: row;
    align-items: center;
    gap: 8px;
    margin-top: 0;
    padding-top: 0;
    border-top: none;
    width: auto;
  }
  
  .version-badge {
    display: none;
  }
  
  .main-area {
    min-height: auto;
  }
  
  .content-area {
    padding: 16px;
  }
  
  .content-wrapper {
    border-radius: var(--radius-lg);
    padding: 20px;
  }
}
</style>
