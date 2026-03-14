function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('mm_theme', theme);

    const toggleButton = document.getElementById('themeToggle');
    if (!toggleButton) {
        return;
    }

    const isDark = theme === 'dark';
    toggleButton.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    toggleButton.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
}

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return '';
    }
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function initNotifications() {
    const bell = document.getElementById('notificationBell');
    const badge = document.getElementById('notificationBadge');
    const panel = document.getElementById('notificationPanel');
    const list = document.getElementById('notificationList');
    const backdrop = document.getElementById('notificationPanelBackdrop');
    const refreshBtn = document.getElementById('notificationRefresh');
    const markAllBtn = document.getElementById('notificationMarkAll');

    if (!bell || !badge || !panel || !list || !backdrop || !refreshBtn || !markAllBtn) {
        return;
    }

    let isOpen = false;
    let pollTimer = null;

    function setBadge(unreadCount) {
        const count = Number(unreadCount) || 0;
        if (count <= 0) {
            badge.hidden = true;
            badge.textContent = '0';
            return;
        }
        badge.hidden = false;
        badge.textContent = count > 99 ? '99+' : String(count);
    }

    function renderNotifications(items) {
        if (!Array.isArray(items) || items.length === 0) {
            list.innerHTML = '<p class="notification-empty">No notifications yet.</p>';
            return;
        }

        const html = items.map((item) => {
            const isUnread = !item.is_read;
            const rowClass = isUnread ? 'notification-item unread' : 'notification-item';
            const dot = isUnread ? '<span class="notification-dot" aria-hidden="true"></span>' : '';
            const linkStart = item.link ? `<a href="${escapeHtml(item.link)}" class="notification-link">` : '<div class="notification-link">';
            const linkEnd = item.link ? '</a>' : '</div>';

            return `
                <article class="${rowClass}" data-notification-id="${item.id}" data-notification-read="${item.is_read ? '1' : '0'}">
                    ${dot}
                    ${linkStart}
                        <div class="notification-title">${escapeHtml(item.title)}</div>
                        ${item.message ? `<p class="notification-message">${escapeHtml(item.message)}</p>` : ''}
                        <span class="notification-time">${escapeHtml(item.created_label || '')}</span>
                    ${linkEnd}
                </article>
            `;
        }).join('');

        list.innerHTML = html;
    }

    function getVisibleUnreadIds() {
        const ids = [];
        list.querySelectorAll('.notification-item[data-notification-read="0"]').forEach((el) => {
            const id = Number(el.getAttribute('data-notification-id'));
            if (Number.isFinite(id) && id > 0) {
                ids.push(id);
            }
        });
        return ids;
    }

    function markVisibleAsRead(ids) {
        if (!Array.isArray(ids) || ids.length === 0) {
            return Promise.resolve();
        }

        return fetch('/api/notifications/read-visible', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids })
        }).catch(() => null);
    }

    function loadNotifications(markVisible) {
        return fetch('/api/notifications?limit=15')
            .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) {
                    throw new Error(data.error || 'Unable to load notifications');
                }

                renderNotifications(data.notifications || []);
                setBadge(data.unread_count || 0);

                if (!markVisible) {
                    return null;
                }

                const visibleUnreadIds = getVisibleUnreadIds();
                if (visibleUnreadIds.length === 0) {
                    return null;
                }

                return markVisibleAsRead(visibleUnreadIds).then(() => {
                    list.querySelectorAll('.notification-item[data-notification-read="0"]').forEach((el) => {
                        const id = Number(el.getAttribute('data-notification-id'));
                        if (visibleUnreadIds.includes(id)) {
                            el.setAttribute('data-notification-read', '1');
                            el.classList.remove('unread');
                            const dot = el.querySelector('.notification-dot');
                            if (dot) {
                                dot.remove();
                            }
                        }
                    });
                    return refreshUnreadCount();
                });
            })
            .catch(() => {
                list.innerHTML = '<p class="notification-empty">Unable to load notifications right now.</p>';
            });
    }

    function refreshUnreadCount() {
        return fetch('/api/notifications/count')
            .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) {
                    return;
                }
                setBadge(data.unread_count || 0);
            })
            .catch(() => null);
    }

    function openPanel() {
        panel.hidden = false;
        backdrop.hidden = false;
        bell.setAttribute('aria-expanded', 'true');
        isOpen = true;
        loadNotifications(true);
    }

    function closePanel() {
        panel.hidden = true;
        backdrop.hidden = true;
        bell.setAttribute('aria-expanded', 'false');
        isOpen = false;
    }

    bell.addEventListener('click', function () {
        if (isOpen) {
            closePanel();
        } else {
            openPanel();
        }
    });

    backdrop.addEventListener('click', closePanel);

    refreshBtn.addEventListener('click', function () {
        loadNotifications(isOpen);
    });

    markAllBtn.addEventListener('click', function () {
        fetch('/api/notifications/read-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
            .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
            .then(({ ok }) => {
                if (!ok) {
                    return;
                }
                return loadNotifications(false).then(() => refreshUnreadCount());
            })
            .catch(() => null);
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && isOpen) {
            closePanel();
        }
    });

    pollTimer = setInterval(function () {
        if (isOpen) {
            loadNotifications(false);
            return;
        }
        refreshUnreadCount();
    }, 20000);

    loadNotifications(false);

    window.addEventListener('beforeunload', function () {
        if (pollTimer) {
            clearInterval(pollTimer);
        }
    });
}

document.addEventListener('click', function (event) {
    if (event.target.matches('.flash-close')) {
        const flash = event.target.closest('.flash');
        if (flash) {
            flash.remove();
        }
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(currentTheme);

    const toggleButton = document.getElementById('themeToggle');
    if (toggleButton) {
        toggleButton.addEventListener('click', function () {
            const activeTheme = document.documentElement.getAttribute('data-theme') || 'light';
            applyTheme(activeTheme === 'dark' ? 'light' : 'dark');
        });
    }

    setTimeout(function () {
        document.querySelectorAll('.flash').forEach(function (flash) {
            flash.style.transition = 'opacity 0.25s ease';
            flash.style.opacity = '0';
            setTimeout(function () {
                flash.remove();
            }, 260);
        });
    }, 5000);

    initNotifications();
});
