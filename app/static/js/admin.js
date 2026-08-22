/**
 * Admin Management Scripts
 * Handles modal workflows, worker assignment, and triage actions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Assign Worker Modal Data Binding
    const assignModal = document.getElementById('assignWorkerModal');
    if (assignModal) {
        assignModal.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            const complaintId = button.getAttribute('data-complaint-id');
            const ticket = button.getAttribute('data-ticket');
            
            const form = document.getElementById('assignWorkerForm');
            form.action = `/admin/complaint/${complaintId}/assign`;
            
            const modalTicket = document.getElementById('assignModalTicket');
            if (modalTicket) modalTicket.textContent = ticket;
        });
    }

    // 2. Reclassify Defect Modal Data Binding
    const reclassifyModal = document.getElementById('reclassifyModal');
    if (reclassifyModal) {
        reclassifyModal.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            const complaintId = button.getAttribute('data-complaint-id');
            const ticket = button.getAttribute('data-ticket');
            const currentDefect = button.getAttribute('data-defect');
            const currentSeverity = button.getAttribute('data-severity');

            const form = document.getElementById('reclassifyForm');
            form.action = `/admin/complaint/${complaintId}/reclassify`;

            const modalTicket = document.getElementById('reclassifyModalTicket');
            if (modalTicket) modalTicket.textContent = ticket;

            const defectSelect = document.getElementById('modalDefectSelect');
            if (defectSelect) defectSelect.value = currentDefect;

            const severitySelect = document.getElementById('modalSeveritySelect');
            if (severitySelect) severitySelect.value = currentSeverity;
        });
    }

    // 3. Mark Resolved Modal Data Binding
    const resolveModal = document.getElementById('resolveComplaintModal');
    if (resolveModal) {
        resolveModal.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            const complaintId = button.getAttribute('data-complaint-id');
            const ticket = button.getAttribute('data-ticket');

            const form = document.getElementById('resolveComplaintForm');
            form.action = `/admin/complaint/${complaintId}/resolve`;

            const modalTicket = document.getElementById('resolveModalTicket');
            if (modalTicket) modalTicket.textContent = ticket;
        });
    }

    // 4. Map Filter Dynamic Change
    const mapDefectFilter = document.getElementById('mapDefectFilter');
    const mapStatusFilter = document.getElementById('mapStatusFilter');

    if (mapDefectFilter && mapStatusFilter && typeof loadMapMarkers === 'function') {
        const triggerMapReload = () => {
            loadMapMarkers(mapDefectFilter.value, mapStatusFilter.value);
        };
        mapDefectFilter.addEventListener('change', triggerMapReload);
        mapStatusFilter.addEventListener('change', triggerMapReload);
    }
});
