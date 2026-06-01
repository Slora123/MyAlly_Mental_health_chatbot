import { THEMES } from '../themes';
import styles from './TypingIndicator.module.css';

export default function TypingIndicator({ theme, botImg }) {
  const t = THEMES[theme];

  return (
    <div className={styles.row} aria-live="polite" aria-label="MyAlly is typing">
      <div className={`${styles.avatar} glass`} aria-hidden="true" style={{ overflow: 'hidden', padding: 0 }}>
        {botImg
          ? <img src={botImg} alt="MyAlly" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          : t.avatar}
      </div>
      <div className={styles.bubble}>
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.dot} />
      </div>
    </div>
  );
}

