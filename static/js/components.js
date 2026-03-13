(function () {
    function setModalState(modal, isOpen) {
        if (!modal) {
            return;
        }

        modal.hidden = !isOpen;
        modal.setAttribute('aria-hidden', isOpen ? 'false' : 'true');

        if (isOpen) {
            document.body.classList.add('modal-open');
        } else if (!document.querySelector('.mm-modal:not([hidden])')) {
            document.body.classList.remove('modal-open');
        }
    }

    function ensureInitialModalState() {
        document.querySelectorAll('.mm-modal').forEach(function (modal) {
            setModalState(modal, false);
        });
    }

    function getModalFromTrigger(trigger) {
        const modalId = trigger.getAttribute('data-modal-id');
        if (modalId) {
            return document.getElementById(modalId);
        }
        return trigger.closest('.mm-modal');
    }

    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        setModalState(modal, true);
    }

    function closeModal(modal) {
        setModalState(modal, false);
    }

    document.addEventListener('click', function (event) {
        const closeTrigger = event.target.closest('[data-modal-close]');
        if (closeTrigger) {
            closeModal(getModalFromTrigger(closeTrigger));
            return;
        }

        const openTrigger = event.target.closest('[data-modal-open]');
        if (openTrigger) {
            openModal(openTrigger.getAttribute('data-modal-open'));
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key !== 'Escape') {
            return;
        }

        const activeModal = document.querySelector('.mm-modal:not([hidden])');
        if (activeModal) {
            closeModal(activeModal);
        }
    });

    document.addEventListener('DOMContentLoaded', function () {
        ensureInitialModalState();
    });

    window.MMComponents = {
        openModal: openModal,
        closeModalById: function (modalId) {
            closeModal(document.getElementById(modalId));
        }
    };
})();
