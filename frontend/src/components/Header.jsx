/**
 * Header.jsx — Top navigation bar
 */

import styles from './Header.module.css'

export default function Header({ isConnected, activeSessions }) {
    return (
        <header className={styles.header} role="banner">
            <div className={styles.inner}>
                {/* Logo */}
                <div className={styles.logo}>
                    <div className={styles.logoIcon} aria-hidden="true">
                        <WaveformIcon />
                    </div>
                    <span className={styles.logoText}>Vaani</span>
                    <span className={styles.logoBadge}>AI</span>
                </div>

                {/* Status indicators */}
                <div className={styles.status}>
                    <div className={`${styles.statusDot} ${isConnected ? styles.statusOnline : styles.statusOffline}`} />
                    <span className={styles.statusText}>
                        {isConnected ? 'Backend online' : 'Backend offline'}
                    </span>
                </div>
            </div>
        </header>
    )
}

function WaveformIcon() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <rect x="2" y="10" width="3" height="4" rx="1.5" fill="currentColor" opacity="0.6" />
            <rect x="7" y="7" width="3" height="10" rx="1.5" fill="currentColor" opacity="0.8" />
            <rect x="12" y="4" width="3" height="16" rx="1.5" fill="currentColor" />
            <rect x="17" y="7" width="3" height="10" rx="1.5" fill="currentColor" opacity="0.8" />
        </svg>
    )
}
