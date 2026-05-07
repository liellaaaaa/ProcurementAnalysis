# ProcurementAnalysis Design System

## Overview
采购分析系统的统一设计规范，采用柔和紫系配色，配合 Element Plus 原生风格进行微调。

## Color Palette

### Primary Colors
| Name | Hex | Usage |
|------|-----|-------|
| Primary | `#8B5CF6` | 主按钮、选中状态、链接 |
| Primary Light | `#A78BFA` | Hover 状态、次要强调 |
| Primary Pale | `#C4B5FD` | 背景点缀、标签 |
| Primary Dark | `#7C3AED` | Active 状态、深色强调 |

### Neutral Colors
| Name | Hex | Usage |
|------|-----|-------|
| Background | `#FAF5FF` | 页面背景（淡紫底色） |
| Surface | `#FFFFFF` | 卡片、弹窗背景 |
| Surface Hover | `#F5F3FF` | Hover 状态背景 |
| Border | `#E4E7ED` | 边框、分割线 |
| Text Primary | `#1E293B` | 主文字 |
| Text Secondary | `#64748B` | 次要文字 |
| Text Muted | `#94A3B4` | 占位符、提示 |

### Semantic Colors
| Name | Hex | Usage |
|------|-----|-------|
| Rise | `#E63946` | 价格上涨、警告 |
| Fall | `#2A9D5C` | 价格下跌、成功 |
| Warning | `#F59E0B` | 警告提示 |
| Info | `#3B82F6` | 信息提示 |

### CSS Variables
```css
:root {
  /* Primary */
  --color-primary: #8B5CF6;
  --color-primary-light: #A78BFA;
  --color-primary-pale: #C4B5FD;
  --color-primary-dark: #7C3AED;
  --color-primary-dim: rgba(139, 92, 246, 0.1);

  /* Background */
  --bg-primary: #FAF5FF;
  --bg-secondary: #FFFFFF;
  --bg-card: #FFFFFF;
  --bg-hover: #F5F3FF;

  /* Text */
  --text-primary: #1E293B;
  --text-secondary: #64748B;
  --text-muted: #94A3B4;

  /* Border */
  --border-color: #E4E7ED;

  /* Semantic */
  --rise-color: #E63946;
  --fall-color: #2A9D5C;
  --warning-color: #F59E0B;
  --info-color: #3B82F6;

  /* Shadow */
  --shadow: 0 2px 12px rgba(139, 92, 246, 0.08);
  --shadow-lg: 0 4px 24px rgba(139, 92, 246, 0.12);
}
```

## Typography

### Font Families
- **Display/Headings**: `Fira Sans` (Google Fonts)
- **Body**: `Fira Sans` (Google Fonts)
- **Monospace/Data**: `Fira Code` (Google Fonts)

### Font Sizes
| Name | Size | Line Height | Usage |
|------|------|-------------|-------|
| xs | 12px | 1.5 | 标签、次要说明 |
| sm | 14px | 1.5 | 正文、按钮 |
| base | 16px | 1.6 | 主要内容 |
| lg | 18px | 1.5 | 副标题 |
| xl | 20px | 1.4 | 卡片标题 |
| 2xl | 24px | 1.3 | 页面标题 |
| 3xl | 30px | 1.2 | 大标题 |

### Font Weights
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

## Spacing

### Spacing Scale
| Name | Value |
|------|-------|
| xs | 4px |
| sm | 8px |
| md | 16px |
| lg | 24px |
| xl | 32px |
| 2xl | 48px |

### Border Radius
| Name | Value |
|------|-------|
| sm | 6px |
| md | 8px |
| lg | 12px |
| xl | 16px |

## Components

### Cards
- Background: `--bg-card`
- Border: 1px solid `--border-color`
- Border Radius: 12px
- Shadow: `--shadow`
- Padding: 20px

### Buttons
- Primary: Background `--color-primary`, text white
- Default: Background white, border `--border-color`, text `--text-primary`
- Border Radius: 8px
- Height: 36px (default), 32px (small), 40px (large)
- Transition: 0.2s ease

### Tables
- Header Background: `--bg-primary`
- Row Hover: `--bg-hover`
- Border: `--border-color`
- Border Radius: 12px (container)

### Forms
- Input Background: `--bg-secondary`
- Input Border: `--border-color`
- Focus Border: `--color-primary`
- Border Radius: 8px

### Navigation
- Height: 64px
- Background: `--bg-secondary`
- Border Bottom: 1px solid `--border-color`
- Active Link: Background `--color-primary-dim`, text `--color-primary`

## Animations

### Durations
| Name | Duration |
|------|----------|
| fast | 150ms |
| normal | 200ms |
| slow | 300ms |

### Easing
- Default: `ease`
- Ease Out: `cubic-bezier(0.16, 1, 0.3, 1)`

### Keyframes
```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  animation: fadeInUp 0.4s ease-out forwards;
}
```

## Icons

- Icon Library: Element Plus Icons (Lucide-based)
- Default Size: 16px (inline), 20px (standalone)
- Color: Inherit from text color

## Responsive Breakpoints

| Name | Min Width |
|------|-----------|
| Mobile | 375px |
| Tablet | 768px |
| Desktop | 1024px |
| Wide | 1440px |

## Best Practices

### Do's
- Use `cursor-pointer` on all interactive elements
- Provide visual feedback on hover (color, shadow changes)
- Use smooth transitions (150-300ms)
- Maintain 4.5:1 color contrast ratio
- Respect `prefers-reduced-motion`

### Don'ts
- Don't use emojis as icons
- Don't use gradients on large backgrounds
- Don't create layout shifts with hover effects
- Don't use shadows that are too prominent