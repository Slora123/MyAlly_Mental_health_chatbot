import { THEMES } from '../themes';
import styles from './MessageBubble.module.css';

function timeStr(value) {
  if (!value) return '';

  let date;
  // Firestore Timestamp comes as {_seconds, _nanoseconds} or {seconds, nanoseconds}
  if (value && typeof value === 'object') {
    const secs = value._seconds ?? value.seconds;
    if (secs !== undefined) {
      date = new Date(secs * 1000);
    }
  }

  // Fall back to ISO string (new messages created client-side)
  if (!date) {
    const normalized = typeof value === 'string' && !value.endsWith('Z') ? value + 'Z' : value;
    date = new Date(normalized);
  }

  if (isNaN(date.getTime())) return '';

  return date.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
}

export default function MessageBubble({ item, theme, botImg, userAvatar, animate }) {
  const isUser = item.role === 'user';
  const t = THEMES[theme];
  const avatar = isUser ? '👤' : '👧';

  return (
    <div
      className={`${styles.row} ${isUser ? styles.user : styles.bot}`}
      style={animate ? { animation: 'msg-in 0.38s cubic-bezier(0.175,0.885,0.32,1.2) both' } : { animation: 'none' }}
    >
      <div className={styles.avatarWrap} aria-hidden="true">
        <div className={`${styles.avatar} ${isUser ? styles.avatarUser : styles.avatarBot}`} style={{ overflow: 'hidden' }}>
          {isUser ? (
            userAvatar ? <img src={userAvatar} className={styles.avatarImg} /> : '👤'
          ) : (
            botImg ? <img src={botImg} className={styles.avatarImg} /> : '👧'
          )}
        </div>
      </div>

      <div className={`${styles.content} ${isUser ? styles.contentUser : styles.contentBot}`}>
        <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleBot}`}>
          <div className={styles.text}>{item.text}</div>
          <time className={`${styles.time} ${isUser ? styles.timeUser : styles.timeBot}`}>
            {timeStr(item.time)}
          </time>
        </div>
      </div>
    </div>
  );
}
