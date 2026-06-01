// Theme configuration for all four moods

export const THEMES = {
  calm: {
    id: 'calm',
    icon: '🌅',
    name: 'Calm Light',
    avatar: '👧',
    status: 'here for you, always 💛',
    statusIcon: '🌅',
  },
  happy: {
    id: 'happy',
    icon: '💗',
    name: 'Soft Pink',
    avatar: '🥰',
    status: 'feeling joyful with you ✨',
    statusIcon: '💗',
  },
  angry: {
    id: 'angry',
    icon: '🔥',
    name: 'Red Mood',
    avatar: '🥺',
    status: "I'm here through the storm 🌩️",
    statusIcon: '🔥',
  },
  night: {
    id: 'night',
    icon: '🌙',
    name: 'Dark Night',
    avatar: '😴',
    status: 'with you through the night 🌙',
    statusIcon: '🌙',
  },
};

// Mood detection rules (client-side, instant)
export const MOOD_RULES = [
  {
    theme: 'angry',
    keywords: [
      'angry', 'anger', 'hate', 'frustrated', 'irritated', 'furious',
      'worst', 'horrible', 'everything is wrong', 'so mad', 'pissed',
      'annoyed', 'rage', 'so angry', 'gussa', 'bahut gussa', 'trast',
      'dimag kharab', 'irritate', 'bakwas', 'bad mood', 'sick of',
    ],
  },
  {
    theme: 'happy',
    keywords: [
      'happy', 'joyful', 'amazing', 'great', 'fantastic', 'so happy',
      'passed', 'won', 'excited', 'yay', 'celebrate', 'love it',
      'wonderful', 'thrilled', 'khush', 'mast', 'badiya', 'awesome',
      'flying colors', 'excited', 'best day', 'feeling good', 'maza',
      'happy today', 'good news',
    ],
  },
  {
    theme: 'night',
    keywords: [
      'lonely', "can't sleep", 'can not sleep', 'late night', 'night',
      'wandering', 'overthinking', 'hopeless', 'numb', 'lost', 'emptiness',
      'midnight', '2am', '3am', 'raat', 'neend nahi', 'what if thoughts',
      'sad', 'depressed', 'depression', 'suicide', 'suiciding', 'kill myself',
      'end it', 'die', 'death', 'hurt myself', 'too much', 'cant go on',
      'cannot go on', 'akelapan', 'dard', 'rone ka man', 'dukh',
      'life is hard', 'give up', 'suicidal', 'ending it',
    ],
  },
];

export function detectThemeFromText(text) {
  const lower = text.toLowerCase();
  for (const rule of MOOD_RULES) {
    if (rule.keywords.some((kw) => lower.includes(kw))) {
      return rule.theme;
    }
  }
  return null;
}
