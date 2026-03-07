/**
 * ProfileView.js
 * Manages the developer profile edit view with structured fields for social links and work history.
 */

const socialLabelMap = {
    github: "GH",
    linkedin: "IN",
    twitter: "TW",
    tiktok: "TT",
    leetcode: "LC",
    kaggle: "KG",
    hackthebox: "HTB",
};

function renderSocialLinks(links = {}) {
    return Object.keys(socialLabelMap)
        .map(
            (key) => `
            <div class="col-md-6 mb-3">
                <label class="form-label small fw-bold text-uppercase">${key}</label>
                <input type="url" id="social-${key}" class="form-control" 
                       placeholder="https://${key}.com/..." value="${links[key] || ""}">
            </div>`
        )
        .join("");
}

export const ProfileView = {
    template(data) {
        const profile = data || {};
        const workHistory = profile.work_history || [];

        return `
            <section id="view-admin-profile" class="py-5" data-test="view-admin-profile">
                <div class="container px-5">
                    <header class="mb-5">
                        <h1 class="fw-bolder">Edit Profile</h1>
                        <p class="lead text-muted">Manage your identity and professional history.</p>
                    </header>

                    <form id="profileForm" class="row g-4">
                        <!-- Identity Section -->
                        <div class="col-12">
                            <div class="card border-0 shadow-sm rounded-4 bg-white">
                                <div class="card-header bg-white border-bottom p-4"><h5 class="mb-0 fw-bold">Identity</h5></div>
                                <div class="card-body p-4">
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label small fw-bold">Full Name</label>
                                            <input type="text" id="p-name" class="form-control" value="${profile.name || ""}" required>
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label small fw-bold">Location</label>
                                            <input type="text" id="p-location" class="form-control" value="${profile.location || ""}" required>
                                        </div>
                                        <div class="col-12 mb-3">
                                            <label class="form-label small fw-bold">Headline Role (Optional Override)</label>
                                            <input type="text" id="p-headline" class="form-control" value="${profile.headline_role || ""}" placeholder="e.g. Senior Software Architect">
                                            <div class="form-text">If left blank, your most recent 'Present' job title will be used.</div>
                                        </div>
                                        <div class="col-12 mb-3">
                                            <label class="form-label small fw-bold">Statement / Bio</label>
                                            <textarea id="p-statement" class="form-control" rows="4" required>${profile.statement || ""}</textarea>
                                        </div>
                                        <div class="col-12">
                                            <label class="form-label small fw-bold">Profile Image URL</label>
                                            <input type="text" id="p-image" class="form-control" value="${profile.image_url || ""}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Social Links -->
                        <div class="col-md-6">
                            <div class="card border-0 shadow-sm rounded-4 bg-white h-100">
                                <div class="card-header bg-white border-bottom p-4"><h5 class="mb-0 fw-bold">Social Links</h5></div>
                                <div class="card-body p-4">
                                    <div class="row">${renderSocialLinks(profile.social_links)}</div>
                                </div>
                            </div>
                        </div>

                        <!-- Skills -->
                        <div class="col-md-6">
                            <div class="card border-0 shadow-sm rounded-4 bg-white h-100">
                                <div class="card-header bg-white border-bottom p-4"><h5 class="mb-0 fw-bold">Skills</h5></div>
                                <div class="card-body p-4">
                                    <label class="form-label small fw-bold">Core Skills (Comma separated)</label>
                                    <textarea id="p-skills" class="form-control" rows="6">${(profile.skills || []).join(", ")}</textarea>
                                </div>
                            </div>
                        </div>

                        <!-- Work History -->
                        <div class="col-12">
                            <div class="card border-0 shadow-sm rounded-4 bg-white">
                                <div class="card-header bg-white border-bottom p-4 d-flex justify-content-between align-items-center">
                                    <h5 class="mb-0 fw-bold">Work History</h5>
                                    <button type="button" class="btn btn-primary btn-sm rounded-pill px-3" id="open-add-work-modal">+ Add Experience</button>
                                </div>
                                <div class="card-body p-0">
                                    <div id="work-history-list" class="list-group list-group-flush p-4">
                                        ${workHistory.map((w, idx) => `
                                            <div class="list-group-item p-4 work-list-item bg-white shadow-sm mb-3 rounded-3" data-idx="${idx}" data-history="${btoa(JSON.stringify(w))}">
                                                <div class="d-flex justify-content-between align-items-start">
                                                    <div>
                                                        <h5 class="fw-bold mb-1">${w.role}</h5>
                                                        <div class="text-primary fw-bold mb-2">${w.company}</div>
                                                        <div class="text-muted small mb-2">
                                                            <span>${w.start_date}</span> &ndash; <span>${w.end_date || "Present"}</span>
                                                            <span class="ms-2">&bull; ${w.location}</span>
                                                        </div>
                                                        <p class="mb-0 small text-muted">${w.description || ""}</p>
                                                    </div>
                                                    <div class="btn-group">
                                                        <button type="button" class="btn btn-sm btn-outline-secondary edit-work-btn">Edit</button>
                                                        <button type="button" class="btn btn-sm btn-outline-danger remove-work-btn">Remove</button>
                                                    </div>
                                                </div>
                                            </div>
                                        `).join("")}
                                        ${workHistory.length === 0 ? '<div class="p-5 text-center text-muted">No experience added yet.</div>' : ""}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="col-12 text-center mt-5">
                            <div id="profile-error" class="alert alert-danger" style="display:none;"></div>
                            <button type="submit" class="btn btn-primary btn-lg px-5 rounded-pill shadow">Save Profile Changes</button>
                        </div>
                    </form>
                </div>

                <!-- Work Entry Modal -->
                <div id="work-modal" class="modal-overlay" style="display:none;">
                    <div class="modal-content card shadow-lg border-0 rounded-4">
                        <div class="card-header bg-white border-bottom p-4 d-flex justify-content-between align-items-center">
                            <h5 class="fw-bolder mb-0" id="work-modal-title">Add Experience</h5>
                            <button type="button" class="btn-close" id="close-work-modal"></button>
                        </div>
                        <div class="card-body p-4">
                            <form id="workEntryForm">
                                <input type="hidden" id="w-idx" value="">
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold">Company</label>
                                        <input type="text" id="w-company" class="form-control" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold">Role</label>
                                        <input type="text" id="w-role" class="form-control" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold">Start Date</label>
                                        <input type="text" id="w-start" class="form-control" placeholder="YYYY-MM" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold">End Date (or 'Present')</label>
                                        <input type="text" id="w-end" class="form-control" placeholder="YYYY-MM or Present">
                                    </div>
                                    <div class="col-12">
                                        <label class="form-label small fw-bold">Location</label>
                                        <input type="text" id="w-location" class="form-control" required>
                                    </div>
                                    <div class="col-12">
                                        <label class="form-label small fw-bold">Description</label>
                                        <textarea id="w-desc" class="form-control" rows="3"></textarea>
                                    </div>
                                    <div class="col-12">
                                        <label class="form-label small fw-bold">Skills (comma separated)</label>
                                        <input type="text" id="w-skills" class="form-control" placeholder="e.g. React, Python, AWS">
                                    </div>
                                </div>
                                <div class="d-flex gap-2 mt-4">
                                    <button type="submit" class="btn btn-primary flex-grow-1" id="save-work-entry">Save Experience</button>
                                    <button type="button" class="btn btn-light" id="cancel-work-modal">Cancel</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </section>
            <style>
                .modal-overlay {
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(30, 30, 30, 0.6); display: flex;
                    align-items: center; justify-content: center; z-index: 1000;
                    backdrop-filter: blur(4px);
                }
                .modal-content { width: 95%; max-width: 600px; }
            </style>`;
    },

    mount: (context) => {
        const fetchAPI = context.api;
        const form = document.getElementById('profileForm');
        if (!form) return;

        const workList = document.getElementById('work-history-list');
        const workModal = document.getElementById('work-modal');
        const workForm = document.getElementById('workEntryForm');

        const openWorkModal = (idx = null) => {
            const titleEl = document.getElementById('work-modal-title');
            if (idx !== null) {
                titleEl.textContent = 'Edit Experience';
                const item = workList.querySelector(`[data-idx="${idx}"]`);
                const data = JSON.parse(atob(item.getAttribute('data-history')));
                document.getElementById('w-idx').value = idx;
                document.getElementById('w-company').value = data.company;
                document.getElementById('w-role').value = data.role;
                document.getElementById('w-start').value = data.start_date;
                document.getElementById('w-end').value = data.end_date || 'Present';
                document.getElementById('w-location').value = data.location;
                document.getElementById('w-desc').value = data.description || '';
                document.getElementById('w-skills').value = (data.skills || []).join(', ');
            } else {
                titleEl.textContent = 'Add Experience';
                workForm.reset();
                document.getElementById('w-idx').value = '';
            }
            workModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        };

        const closeWorkModal = () => {
            workModal.style.display = 'none';
            document.body.style.overflow = '';
        };

        document.getElementById('open-add-work-modal').onclick = () => openWorkModal();
        document.getElementById('close-work-modal').onclick = closeWorkModal;
        document.getElementById('cancel-work-modal').onclick = closeWorkModal;

        workList.onclick = (e) => {
            const item = e.target.closest('.work-list-item');
            if (!item) return;
            const idx = item.getAttribute('data-idx');

            if (e.target.classList.contains('remove-work-btn')) {
                if (confirm('Remove this experience entry?')) item.remove();
            } else if (e.target.classList.contains('edit-work-btn')) {
                openWorkModal(idx);
            }
        };

        workForm.onsubmit = (e) => {
            e.preventDefault();
            const idx = document.getElementById('w-idx').value;
            const entry = {
                company: document.getElementById('w-company').value,
                role: document.getElementById('w-role').value,
                start_date: document.getElementById('w-start').value,
                end_date: document.getElementById('w-end').value,
                location: document.getElementById('w-location').value,
                description: document.getElementById('w-desc').value,
                skills: document.getElementById('w-skills').value.split(',').map(s => s.trim()).filter(s => s)
            };

            const html = `
                <div class="list-group-item p-4 work-list-item bg-white shadow-sm mb-3 rounded-3" data-idx="${idx || Date.now()}" data-history="${btoa(JSON.stringify(entry))}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5 class="fw-bold mb-1">${entry.role}</h5>
                            <div class="text-primary fw-bold mb-2">${entry.company}</div>
                            <div class="text-muted small mb-2">
                                <span>${entry.start_date}</span> &ndash; <span>${entry.end_date || "Present"}</span>
                                <span class="ms-2">&bull; ${entry.location}</span>
                            </div>
                            <p class="mb-0 small text-muted">${entry.description || ""}</p>
                        </div>
                        <div class="btn-group">
                            <button type="button" class="btn btn-sm btn-outline-secondary edit-work-btn">Edit</button>
                            <button type="button" class="btn btn-sm btn-outline-danger remove-work-btn">Remove</button>
                        </div>
                    </div>
                </div>`;

            if (idx !== "") {
                const oldItem = workList.querySelector(`[data-idx="${idx}"]`);
                oldItem.outerHTML = html;
            } else {
                const emptyMsg = workList.querySelector('.text-muted.p-5');
                if (emptyMsg) emptyMsg.remove();
                workList.insertAdjacentHTML('beforeend', html);
            }
            closeWorkModal();
        };

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const social_links = {};
            Object.keys(socialLabelMap).forEach(key => {
                const val = document.getElementById(`social-${key}`).value;
                if (val) social_links[key] = val;
            });

            const work_history = Array.from(workList.querySelectorAll('.work-list-item')).map(item => {
                return JSON.parse(atob(item.getAttribute('data-history')));
            });

            const profileData = {
                name: document.getElementById('p-name').value,
                location: document.getElementById('p-location').value,
                headline_role: document.getElementById('p-headline').value,
                statement: document.getElementById('p-statement').value,
                image_url: document.getElementById('p-image').value,
                skills: document.getElementById('p-skills').value.split(',').map(s => s.trim()).filter(s => s),
                social_links,
                work_history
            };

            try {
                await fetchAPI('/api/content/profile', {
                    method: 'PUT',
                    body: JSON.stringify(profileData)
                });
                context.navigate('/home');
            } catch (err) {
                const errEl = document.getElementById('profile-error');
                errEl.textContent = "Save failed: " + err.message;
                errEl.style.display = 'block';
                window.scrollTo(0, 0);
            }
        });
    }
};
