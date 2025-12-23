# UI Design System

## Overview
Professional UI design system for the Surgical Outcomes Database application with standardized components and layout patterns.

## Components

### 1. Layout Component (`/frontend/src/components/Layout.tsx`)
Master page wrapper providing consistent structure across all pages.

**Features:**
- Sticky header with logo and branding ("Surgical Outcomes Database & Analytics")
- Navigation bar with active route highlighting
- User menu showing full name, role, and logout button
- Main content area with max-width container (max-w-7xl)
- Footer with copyright, version, and logged-in user email

**Usage:**
```tsx
<Layout>
  <YourPageContent />
</Layout>
```

### 2. PageHeader Component (`/frontend/src/components/PageHeader.tsx`)
Standardized page title section for consistent page headers.

**Props:**
- `title` (string, required): Main heading text
- `subtitle` (string, optional): Descriptive subtitle
- `icon` (ReactNode, optional): Icon displayed in colored circle
- `action` (ReactNode, optional): Action button or component (e.g., "+ Add New")

**Usage:**
```tsx
<PageHeader
  title="Dashboard"
  subtitle="Welcome to the system"
  icon={<IconSVG />}
  action={<Button>Create</Button>}
/>
```

### 3. Card Component (`/frontend/src/components/Card.tsx`)
Reusable content container with consistent styling.

**Props:**
- `children` (ReactNode, required): Card content
- `className` (string, optional): Additional CSS classes
- `padding` ('none' | 'small' | 'medium' | 'large', optional, default: 'medium')
- `hover` (boolean, optional): Enable hover shadow effect

**Padding Sizes:**
- none: No padding (useful for tables)
- small: p-4
- medium: p-6 (default)
- large: p-8

**CardHeader Subcomponent:**
```tsx
<Card>
  <CardHeader 
    title="Section Title"
    subtitle="Optional description"
    action={<Button>Action</Button>}
  />
  <CardContent />
</Card>
```

### 4. Button Component (`/frontend/src/components/Button.tsx`)
Standardized button with multiple variants and sizes.

**Props:**
- `children` (ReactNode, required): Button text/content
- `variant` ('primary' | 'secondary' | 'success' | 'danger' | 'outline', default: 'primary')
- `size` ('small' | 'medium' | 'large', default: 'medium')
- `icon` (ReactNode, optional): Icon displayed before text
- All standard button HTML attributes (onClick, disabled, type, etc.)

**Variants:**
- **primary**: Blue background, white text (main actions)
- **secondary**: Gray background, white text (neutral actions)
- **success**: Green background, white text (confirmations)
- **danger**: Red background, white text (deletions/warnings)
- **outline**: White background, gray border and text (secondary actions)

**Sizes:**
- small: px-3 py-1.5 text-sm
- medium: px-4 py-2 text-sm
- large: px-6 py-3 text-base

**Usage:**
```tsx
<Button variant="primary" size="medium" onClick={handleClick}>
  Save Changes
</Button>

<Button variant="danger" size="small" icon={<TrashIcon />}>
  Delete
</Button>
```

## Design Principles

### 1. Consistency
- All pages use the same Layout wrapper
- All page titles use PageHeader component
- All content sections use Card components
- All buttons use Button component with standardized variants

### 2. Color Palette
- **Primary (Blue)**: Main actions, branding, active states
  - bg-blue-600, text-blue-600, border-blue-600
- **Secondary (Gray)**: Neutral actions, text, backgrounds
  - bg-gray-600, text-gray-500, border-gray-300
- **Success (Green)**: Confirmations, positive states
  - bg-green-600, text-green-600
- **Danger (Red)**: Deletions, errors, warnings
  - bg-red-600, text-red-600
- **Purple**: Special metrics, highlights
  - bg-purple-600, text-purple-600

### 3. Typography
- **Page Titles**: text-3xl font-bold text-gray-900
- **Section Headings**: text-lg font-medium text-gray-900
- **Body Text**: text-sm text-gray-700
- **Subtitles**: text-sm text-gray-500

### 4. Spacing
- **Page Container**: py-6 space-y-6 (vertical spacing between sections)
- **Card Padding**: p-6 (medium, default)
- **Component Gaps**: gap-6 (grid layouts)
- **Form Fields**: space-y-4 (vertical form spacing)

### 5. Shadows & Effects
- **Cards**: shadow (default), hover:shadow-lg (with hover prop)
- **Buttons**: Focus rings with focus:ring-2 focus:ring-offset-2
- **Transitions**: transition-colors, transition-shadow

## Page Structure Pattern

Standard pattern for all authenticated pages:

```tsx
import { PageHeader } from '../components/PageHeader'
import { Card } from '../components/Card'
import { Button } from '../components/Button'

export function YourPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Page Title"
        subtitle="Description of the page"
        icon={<IconSVG />}
        action={<Button variant="primary">+ Add New</Button>}
      />

      {/* Stats or Quick Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card hover>
          <StatContent />
        </Card>
        {/* More stat cards... */}
      </div>

      {/* Main Content */}
      <Card>
        <MainPageContent />
      </Card>

      {/* Additional Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <SectionContent />
        </Card>
        {/* More sections... */}
      </div>
    </div>
  )
}
```

## Responsive Design

### Breakpoints (Tailwind defaults)
- **sm**: 640px
- **md**: 768px
- **lg**: 1024px
- **xl**: 1280px
- **2xl**: 1536px

### Common Patterns
- Grid layouts: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- Responsive padding: `px-4 sm:px-6 lg:px-8`
- Container max-width: `max-w-7xl mx-auto`

## Current Page Implementations

### 1. HomePage (`/frontend/src/pages/HomePage.tsx`)
- Dashboard with welcome message
- 3 stat cards (Total Patients, Total Surgeries, This Month)
- User profile card
- Quick actions section
- Recent activity section (empty state)

### 2. PatientsPage (`/frontend/src/pages/PatientsPage.tsx`)
- PageHeader with "+ Add Patient" button
- Empty state with call-to-action
- Ready for patient list/form implementation

### 3. SurgeriesPage (`/frontend/src/pages/SurgeriesPage.tsx`)
- PageHeader with "+ Record Surgery" button
- Empty state with call-to-action
- Ready for surgery list/form implementation

### 4. ReportsPage (`/frontend/src/pages/ReportsPage.tsx`)
- PageHeader for analytics
- 3 stat cards (Total Procedures, Success Rate, Average Duration)
- Empty state message
- Ready for charts/visualizations

### 5. AdminPage (`/frontend/src/pages/AdminPage.tsx`)
- PageHeader with "+ Create User" button
- Collapsible user creation form in Card
- User table in Card with no padding (for full-width table)
- Action buttons (Activate/Deactivate, Delete) using Button component
- Role and status badges
- Empty state handling

### 6. LoginPage (`/frontend/src/pages/LoginPage.tsx`)
- Standalone page (no Layout wrapper)
- Custom styling with centered card
- Toggle between login and register forms
- Logo and branding

## Future Enhancements

### Planned Components
- **Modal/Dialog**: For confirmations and forms
- **Alert/Notification**: Toast notifications for actions
- **Table**: Standardized data table component
- **Form**: Form wrapper with validation display
- **Input**: Standardized input fields
- **Select**: Dropdown select component
- **DatePicker**: Date selection component
- **Badge**: Status indicators and labels
- **Tabs**: Tabbed content sections
- **Tooltip**: Contextual help
- **Loading**: Loading states and spinners

### Accessibility
- ARIA labels on all interactive elements
- Keyboard navigation support
- Focus management
- Screen reader compatibility
- Color contrast compliance (WCAG AA)

### Dark Mode
- Consider adding dark mode support
- Use Tailwind's dark: variant
- Store user preference in localStorage

## Development Guidelines

### Adding New Pages
1. Import Layout, PageHeader, Card, Button
2. Follow the standard page structure pattern
3. Use consistent spacing (space-y-6 for sections)
4. Apply responsive grid layouts
5. Include empty states for new features

### Creating Forms
1. Wrap in Card component
2. Use grid layouts for form fields (grid-cols-1 md:grid-cols-2)
3. Apply consistent spacing (space-y-4)
4. Add required field indicators (* in red)
5. Use Button component for form actions
6. Include validation error displays

### Building Tables
1. Wrap table in Card with padding="none"
2. Use standard table structure with thead/tbody
3. Add hover effects (hover:bg-gray-50 on tr)
4. Include empty state handling
5. Use Button component for row actions
6. Add responsive overflow (overflow-x-auto)

### Empty States
1. Center content with py-12
2. Include large icon (w-16 h-16 text-gray-300)
3. Add descriptive heading (text-lg font-medium)
4. Provide helpful message (text-gray-500)
5. Include call-to-action button when appropriate

## Technical Notes

### Tailwind CSS Configuration
- Using Tailwind CSS 3.4.17
- Custom configuration in `tailwind.config.js`
- Purge unused styles in production

### React Router Integration
- Layout wraps protected route content
- Navigation uses react-router-dom Link
- Active route highlighting with useLocation

### Authentication Integration
- Layout displays user info from AuthContext
- Logout button in user menu
- Role-based navigation (Admin link only for admins)

### Performance
- Components are lightweight and reusable
- No external UI libraries (reduces bundle size)
- Tailwind purges unused CSS in production
- Layout component memoization opportunity

## Maintenance

### Updating Design System
1. Make changes to component files in `/frontend/src/components/`
2. Update this directive with changes
3. Test all pages to ensure consistency
4. Commit with descriptive message
5. Update any dependent components

### Version History
- **v1.0** (Current): Initial design system with Layout, PageHeader, Card, Button components
- All pages updated to use new design system
- Responsive design implemented
- Professional appearance achieved
