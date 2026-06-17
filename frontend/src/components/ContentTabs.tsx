import { useState, type ReactNode } from 'react'
import type { Language } from '../types'

export type ContentTabId = 'pdf' | 'answers'

interface ContentTabsProps {
  language: Language
  pdfPanel: ReactNode
  answersPanel: ReactNode
}

export function ContentTabs({ language, pdfPanel, answersPanel }: ContentTabsProps) {
  const [activeTab, setActiveTab] = useState<ContentTabId>('pdf')

  const tabs: { id: ContentTabId; label: string }[] = [
    {
      id: 'pdf',
      label: language === 'vi' ? 'Xem PDF trực tiếp' : 'PDF Preview Live',
    },
    {
      id: 'answers',
      label: language === 'vi' ? 'Thông tin đã điền' : 'Filled Information',
    },
  ]

  return (
    <section className="content-tabs">
      <div className="tab-bar" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tab-panel" role="tabpanel">
        {activeTab === 'pdf' ? pdfPanel : answersPanel}
      </div>
    </section>
  )
}
