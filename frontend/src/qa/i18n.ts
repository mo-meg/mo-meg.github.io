import type { Category, Lang } from './types'

export const ui: Record<
  Lang,
  {
    langName: string
    title: string
    subtitle: string
    welcome: string
    suggested: string
    categories: Record<Category, string>
    placeholder: string
    send: string
    clear: string
    close: string
    copy: string
    copied: string
    sources: string
    related: string
    fallback: string
    didYouMean: string
    emailMe: string
    emailSubject: string
    emailBody: (q: string) => string
    linkedin: string
    footer: string
    draft: string
    back: string
  }
> = {
  en: {
    langName: 'English',
    title: 'Ask about Mohamed',
    subtitle: 'Prepared answers · curated by Mohamed',
    welcome:
      "Hi! I'm Mohamed's portfolio assistant. Pick a question below or type your own — I'll show the answer Mohamed prepared for it.",
    suggested: 'Suggested questions',
    categories: {
      profile: 'Profile',
      experience: 'Experience',
      projects: 'Projects',
      skills: 'Skills',
      cloud: 'Cloud & infrastructure',
      education: 'Education',
      contact: 'Contact & hiring',
    },
    placeholder: 'Ask in English, Deutsch, or العربية…',
    send: 'Send',
    clear: 'Clear conversation',
    close: 'Close assistant',
    copy: 'Copy',
    copied: 'Copied',
    sources: 'Sources',
    related: 'Related questions',
    fallback: "I don't have a prepared answer for that yet — Mohamed is happy to answer it personally.",
    didYouMean: 'Did you mean…',
    emailMe: 'Ask Mohamed by email',
    emailSubject: 'Question from your portfolio',
    emailBody: (q) => `Hi Mohamed,\n\nI have a question:\n\n${q}\n\n`,
    linkedin: 'LinkedIn',
    footer: 'Answers are prepared and reviewed by Mohamed. Your questions are matched in your browser and are not sent anywhere.',
    draft: 'Draft — not published',
    back: 'Show all questions',
  },
  de: {
    langName: 'Deutsch',
    title: 'Fragen zu Mohamed',
    subtitle: 'Vorbereitete Antworten · kuratiert von Mohamed',
    welcome:
      'Hallo! Ich bin Mohameds Portfolio-Assistent. Wählen Sie unten eine Frage oder stellen Sie Ihre eigene – ich zeige Ihnen die Antwort, die Mohamed dafür vorbereitet hat.',
    suggested: 'Vorgeschlagene Fragen',
    categories: {
      profile: 'Profil',
      experience: 'Berufserfahrung',
      projects: 'Projekte',
      skills: 'Kenntnisse',
      cloud: 'Cloud & Infrastruktur',
      education: 'Ausbildung',
      contact: 'Kontakt & Einstellung',
    },
    placeholder: 'Fragen auf Deutsch, English oder العربية…',
    send: 'Senden',
    clear: 'Unterhaltung löschen',
    close: 'Assistent schließen',
    copy: 'Kopieren',
    copied: 'Kopiert',
    sources: 'Quellen',
    related: 'Ähnliche Fragen',
    fallback: 'Dazu habe ich noch keine vorbereitete Antwort – Mohamed beantwortet Ihre Frage gern persönlich.',
    didYouMean: 'Meinten Sie…',
    emailMe: 'Mohamed per E-Mail fragen',
    emailSubject: 'Frage über Ihr Portfolio',
    emailBody: (q) => `Hallo Mohamed,\n\nich habe eine Frage:\n\n${q}\n\n`,
    linkedin: 'LinkedIn',
    footer: 'Die Antworten wurden von Mohamed vorbereitet und geprüft. Ihre Fragen werden nur in Ihrem Browser abgeglichen und nirgendwohin gesendet.',
    draft: 'Entwurf – nicht veröffentlicht',
    back: 'Alle Fragen anzeigen',
  },
  ar: {
    langName: 'العربية',
    title: 'اسأل عن محمد',
    subtitle: 'إجابات معدّة مسبقًا · من إعداد محمد',
    welcome: 'مرحبًا! أنا مساعد محمد في موقعه الشخصي. اختر سؤالًا من الأسئلة أدناه أو اكتب سؤالك، وسأعرض لك الإجابة التي أعدّها محمد.',
    suggested: 'أسئلة مقترحة',
    categories: {
      profile: 'الملف الشخصي',
      experience: 'الخبرة المهنية',
      projects: 'المشاريع',
      skills: 'المهارات',
      cloud: 'السحابة والبنية التحتية',
      education: 'التعليم',
      contact: 'التواصل والتوظيف',
    },
    placeholder: 'اكتب سؤالك بالعربية أو English أو Deutsch…',
    send: 'إرسال',
    clear: 'مسح المحادثة',
    close: 'إغلاق المساعد',
    copy: 'نسخ',
    copied: 'تم النسخ',
    sources: 'المصادر',
    related: 'أسئلة ذات صلة',
    fallback: 'لا توجد لديّ إجابة معدّة لهذا السؤال بعد، ويسعد محمد أن يجيبك عليه شخصيًا.',
    didYouMean: 'هل تقصد…',
    emailMe: 'اسأل محمد عبر البريد الإلكتروني',
    emailSubject: 'سؤال من موقعك الشخصي',
    emailBody: (q) => `مرحبًا محمد،\n\nلديّ سؤال:\n\n${q}\n\n`,
    linkedin: 'لينكدإن',
    footer: 'الإجابات من إعداد محمد ومراجعته. تتم مطابقة أسئلتك داخل متصفحك فقط ولا تُرسل إلى أي جهة.',
    draft: 'مسودة — غير منشورة',
    back: 'عرض جميع الأسئلة',
  },
}

export function browserLang(): Lang {
  const langs = typeof navigator !== 'undefined' ? navigator.languages ?? [navigator.language] : []
  for (const l of langs) {
    const code = l.slice(0, 2).toLowerCase()
    if (code === 'de' || code === 'ar' || code === 'en') return code
  }
  return 'en'
}
