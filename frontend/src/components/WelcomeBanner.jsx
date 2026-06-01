import styles from './WelcomeBanner.module.css';

const CHIPS = [
  { emoji: '😓', text: 'Exams se bahut stress ho raha hai' },
  { emoji: '💤', text: "I haven't slept properly in days" },
  { emoji: '😔', text: 'Feeling lonely lately' },
  { emoji: '🧠', text: 'What is anxiety?' },
  { emoji: '💬', text: 'I just want to talk' },
];

export default function WelcomeBanner({ onChipClick }) {
  return (
    <div className={styles.banner} role="region" aria-label="Welcome message">
      <div className={styles.emojiHero} aria-hidden="true">😊</div>
      <h3 className={styles.title}>Hey! I'm MyAlly 👋</h3>
      <p className={styles.subtitle}>
        Your chill mental-health companion.
        <br />
        <span className={styles.hint}>English, Hinglish, ya Minglish — sab chalega!</span>
      </p>
      <div className={styles.chips}>
        {CHIPS.map((c) => (
          <button
            key={c.text}
            className={styles.chip}
            onClick={() => onChipClick(c.emoji + ' ' + c.text)}
          >
            {c.emoji} {c.text}
          </button>
        ))}
      </div>
    </div>
  );
}
