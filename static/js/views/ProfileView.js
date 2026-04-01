/**
 * ProfileView.js
 * Revamped profile management with tabbed interface and user settings.
 */

import { renderMarkdown } from '../utils/SecurityUtils.js';

const socialIconMap = {
    github: "bi-github",
    linkedin: "bi-linkedin",
    twitter: "bi-twitter-x",
    tiktok: "bi-tiktok",
    leetcode: "bi-code-slash",
    kaggle: "bi-graph-up",
    hackthebox: "bi-shield-lock",
};

const encodeHistory = (entry) => encodeURIComponent(JSON.stringify(entry));

const decodeHistory = (value) => {
    try {
        return JSON.parse(decodeURIComponent(value));
    } catch (err) {
        console.error("Failed to decode work history entry.", err);
        return null;
    }
};

function renderSocialLinkInputs(links = {}) {
    return Object.keys(socialIconMap)
        .map(
            (key) => `
            <div class="col-md-6 mb-3">
                <label class="form-label small fw-bold text-uppercase d-flex align-items-center gap-2">
                    <i class="bi ${socialIconMap[key]}"></i> ${key}
                </label>
                <input type="url" id="social-${key}" class="form-control" 
                       placeholder="https://${key}.com/..." value="${links[key] || ""}">
            </div>`
        )
        .join("");
}

export const ProfileView = {
    template(data, auth) {
        const profile = data || {};
        const workHistory = profile.work_history || [];

        return `
            <section id="view-admin-profile" class="py-5" data-test="view-admin-profile">
                <div class="container px-3 px-lg-5">
                    <header class="mb-5 d-flex justify-content-between align-items-end">
                        <div>
                            <h1 class="fw-bolder mb-1">Account Settings</h1>
                            <p class="lead text-muted mb-0">Manage your professional identity and security.</p>
                        </div>
                        <div class="d-none d-md-block">
                             <span class="badge bg-light text-dark border p-2">Role: ${auth.user?.role || 'Guest'}</span>
                        </div>
                    </header>

                    <!-- Settings Tabs -->
                    <ul class="nav nav-pills mb-4 gap-2" id="profileTabs" role="tablist">
                        <li class="nav-item">
                            <button class="btn btn-primary active rounded-pill px-4" id="identity-tab" data-bs-toggle="pill" data-bs-target="#tab-identity" type="button">
                                <i class="bi bi-person-badge mr-2"></i> Identity
                            </button>
                        </li>
                        <li class="nav-item">
                            <button class="btn btn-outline-dark rounded-pill px-4" id="experience-tab" data-bs-toggle="pill" data-bs-target="#tab-experience" type="button">
                                <i class="bi bi-briefcase mr-2"></i> Experience
                            </button>
                        </li>
                        <li class="nav-item">
                            <button class="btn btn-outline-dark rounded-pill px-4" id="security-tab" data-bs-toggle="pill" data-bs-target="#tab-security" type="button">
                                <i class="bi bi-shield-lock mr-2"></i> Security
                            </button>
                        </li>
                    </ul>

                    <div class="tab-content">
                        <!-- Identity Tab -->
                        <div class="tab-pane fade show active" id="tab-identity">
                            <form id="profileForm" class="row g-4">
                                <div class="col-12">
                                    <div class="card border-0 shadow-sm rounded-4 bg-white mb-4">
                                        <div class="card-header bg-white border-bottom p-4"><h5 class="mb-0 fw-bold">General Information</h5></div>
                                        <div class="card-body p-4">
                                            <div class="row">
                                                <div class="col-md-6 mb-3">
                                                    <label class="form-label small fw-bold">Full Display Name</label>
                                                    <input type="text" id="p-name" class="form-control" value="${profile.name || ""}" required>
                                                </div>
                                                <div class="col-md-6 mb-3">
                                                    <label class="form-label small fw-bold">Location</label>
                                                    <input type="text" id="p-location" class="form-control" value="${profile.location || ""}" required>
                                                </div>
                                                <div class="col-12 mb-3">
                                                    <label class="form-label small fw-bold">Headline Role (Hero Title)</label>
                                                    <input type="text" id="p-headline" class="form-control" value="${profile.headline_role || ""}" placeholder="e.g. Senior Software Architect">
                                                    <div class="form-text">Used as the main title on the homepage.</div>
                                                </div>
                                                <div class="col-12 mb-3">
                                                    <label class="form-label small fw-bold">Statement / Professional Bio</label>
                                                    <textarea id="p-statement" class="form-control" rows="4" required>${profile.statement || ""}</textarea>
                                                </div>
                                                <div class="col-12">
                                                    <label class="form-label small fw-bold">Profile Image</label>
                                                    <div class="d-flex align-items-center gap-3 p-3 border rounded-3 bg-light">
                                                        <img id="p-image-preview" src="${profile.image_url || "/static/uploads/placeholder-profile.png"}" 
                                                             class="rounded-circle shadow-sm border bg-white" style="width: 80px; height: 80px; object-fit: cover;"
                                                             onerror="this.src='/static/uploads/placeholder-profile.png'">
                                                        <div class="flex-grow-1">
                                                            <div class="input-group">
                                                                <input type="text" id="p-image" class="form-control" value="${profile.image_url || ""}" placeholder="/static/uploads/..." readonly>
                                                                <input type="file" id="p-image-file" class="d-none" accept="image/*">
                                                                <button type="button" class="btn btn-dark" id="p-image-upload-btn">
                                                                    <i class="bi bi-cloud-upload mr-2"></i> Upload
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="row g-4">
                                        <div class="col-lg-7">
                                            <div class="card border-0 shadow-sm rounded-4 bg-white h-100">
                                                <div class="card-header bg-white border-bottom p-4"><h5 class="mb-0 fw-bold">Social & Professional Links</h5></div>
                                                <div class="card-body p-4">
                                                    <div class="row">${renderSocialLinkInputs(profile.social_links)}</div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-lg-5">
                                            <div class="card border-0 shadow-sm rounded-4 bg-white h-100">
                                                <div class="card-header bg-white border-bottom p-4"><h5 class="mb-0 fw-bold">Core Skills</h5></div>
                                                <div class="card-body p-4 text-center">
                                                    <p class="small text-muted mb-3">Enter skills separated by commas.</p>
                                                    <textarea id="p-skills" class="form-control mb-3" rows="8" placeholder="Python, Flask, Docker...">${(profile.skills || []).join(", ")}</textarea>
                                                    <div id="skills-preview" class="d-flex flex-wrap gap-2 justify-content-center">
                                                        ${(profile.skills || []).map(s => `<span class="badge bg-primary">${s}</span>`).join('')}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="text-end mt-5">
                                        <div id="profile-error" class="alert alert-danger mb-3" style="display:none;"></div>
                                        <button type="submit" class="btn btn-success btn-lg px-5 rounded-pill shadow">Save All Identity Changes</button>
                                    </div>
                                </div>
                            </form>
                        </div>

                        <!-- Experience Tab -->
                        <div class="tab-pane fade" id="tab-experience">
                            <div id="experience-error" class="alert alert-danger mb-3" style="display:none;"></div>
                            <div id="experience-success" class="alert alert-success mb-3" style="display:none;"></div>
                            <div class="card border-0 shadow-sm rounded-4 bg-white">
                                <div class="card-header bg-white border-bottom p-4 d-flex justify-content-between align-items-center">
                                    <h5 class="mb-0 fw-bold">Professional History</h5>
                                    <button type="button" class="btn btn-primary btn-sm rounded-pill px-4" id="open-add-work-modal">
                                        <i class="bi bi-plus-lg mr-2"></i> Add Entry
                                    </button>
                                </div>
                                <div class="card-body p-0">
                                    <div id="work-history-list" class="list-group list-group-flush p-4">
                                        ${workHistory.map((w, idx) => `
                                            <div class="list-group-item p-4 work-list-item border rounded-3 bg-white shadow-sm mb-3" data-idx="${idx}" data-history="${encodeHistory(w)}">
                                                <div class="d-flex justify-content-between align-items-start">
                                                    <div class="flex-grow-1">
                                                        <div class="d-flex align-items-center gap-2 mb-1">
                                                            <h5 class="fw-bold mb-0">${w.role}</h5>
                                                            <span class="badge bg-light text-dark border small">${w.end_date === 'Present' ? 'Current' : 'Past'}</span>
                                                        </div>
                                                        <div class="text-primary fw-bold mb-2"><i class="bi bi-building mr-1"></i> ${w.company}</div>
                                                        <div class="text-muted small mb-3">
                                                            <i class="bi bi-calendar3 mr-1"></i> <span>${w.start_date}</span> &ndash; <span>${w.end_date || "Present"}</span>
                                                            <span class="ms-3"><i class="bi bi-geo-alt mr-1"></i> ${w.location}</span>
                                                        </div>
                                                        <div class="mb-0 small text-muted text-justify markdown" style="max-width: 800px;">${renderMarkdown(w.description || "")}</div>
                                                    </div>
                                                    <div class="btn-group ms-3">
                                                        <button type="button" class="btn btn-sm btn-outline-secondary edit-work-btn" title="Edit"><i class="bi bi-pencil"></i></button>
                                                        <button type="button" class="btn btn-sm btn-outline-danger remove-work-btn" title="Delete"><i class="bi bi-trash"></i></button>
                                                    </div>
                                                </div>
                                            </div>
                                        `).join("")}
                                        ${workHistory.length === 0 ? '<div class="p-5 text-center text-muted"><i class="bi bi-inbox display-4 d-block mb-3"></i>No history records found.</div>' : ""}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Security Tab -->
                        <div class="tab-pane fade" id="tab-security">
                            <div class="row g-4">
                                <div class="col-lg-6">
                                    <div class="card border-0 shadow-sm rounded-4 bg-white">
                                        <div class="card-header bg-white border-bottom p-4">
                                            <h5 class="mb-0 fw-bold"><i class="bi bi-key mr-2"></i> Change Password</h5>
                                        </div>
                                        <div class="card-body p-4">
                                            <form id="changePasswordForm">
                                                <div class="mb-3">
                                                    <label class="form-label small fw-bold">Current Password</label>
                                                    <input type="password" id="current-password" class="form-control" required>
                                                </div>
                                                <hr>
                                                <div class="mb-3">
                                                    <label class="form-label small fw-bold">New Password</label>
                                                    <input type="password" id="new-password" class="form-control" required>
                                                    <div class="form-text small">Must be at least 8 characters with 1 number and 1 special character.</div>
                                                </div>
                                                <div class="mb-4">
                                                    <label class="form-label small fw-bold">Confirm New Password</label>
                                                    <input type="password" id="confirm-password" class="form-control" required>
                                                </div>
                                                <div id="password-error" class="alert alert-danger mb-3" style="display:none;"></div>
                                                <div id="password-success" class="alert alert-success mb-3" style="display:none;">Password changed successfully!</div>
                                                <button type="submit" class="btn btn-dark w-100 rounded-pill py-3">Update Security Credentials</button>
                                            </form>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-lg-6">
                                    <div class="card border-0 shadow-sm rounded-4 bg-white mb-4">
                                        <div class="card-header bg-white border-bottom p-4">
                                            <h5 class="mb-0 fw-bold"><i class="bi bi-envelope mr-2"></i> Change Email</h5>
                                        </div>
                                        <div class="card-body p-4">
                                            <form id="changeEmailForm">
                                                <div class="mb-3">
                                                    <label class="form-label small fw-bold">Current Email</label>
                                                    <input type="email" class="form-control" value="${auth.user?.email || ""}" readonly disabled>
                                                </div>
                                                <div class="mb-4">
                                                    <label class="form-label small fw-bold">New Email Address</label>
                                                    <input type="email" id="new-email" class="form-control" required>
                                                </div>
                                                <div id="email-error" class="alert alert-danger mb-3" style="display:none;"></div>
                                                <div id="email-success" class="alert alert-success mb-3" style="display:none;">Email updated successfully!</div>
                                                <button type="submit" class="btn btn-outline-dark w-100 rounded-pill py-3">Update Email Address</button>
                                            </form>
                                        </div>
                                    </div>

                                    <div class="card border-danger shadow-sm rounded-4 bg-white">
                                        <div class="card-header bg-white border-bottom p-4 text-danger">
                                            <h5 class="mb-0 fw-bold"><i class="bi bi-exclamation-triangle mr-2"></i> Danger Zone</h5>
                                        </div>
                                        <div class="card-body p-4">
                                            <p class="small text-muted mb-4">Permanently delete your account and all associated data. This action is irreversible.</p>
                                            <button type="button" id="delete-account-btn" class="btn btn-outline-danger w-100 rounded-pill py-3">Delete My Account</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Re-authentication Modal (Shared for Email Change / Deletion) -->
                <div id="reauth-modal" class="modal-overlay" style="display:none;">
                    <div class="modal-content card shadow-lg border-0 rounded-4" style="max-width: 450px;">
                        <div class="card-header bg-white border-bottom p-4 d-flex justify-content-between align-items-center">
                            <h5 class="fw-bolder mb-0" id="reauth-modal-title">Confirm Identity</h5>
                            <button type="button" class="btn-close" id="close-reauth-modal"></button>
                        </div>
                        <div class="card-body p-4 text-center">
                            <p id="reauth-message" class="mb-4">Please confirm your current password to proceed with this sensitive action.</p>
                            <form id="reauthForm">
                                <input type="password" id="reauth-password" class="form-control form-control-lg mb-3" placeholder="Current Password" required>
                                <div id="reauth-error" class="alert alert-danger mb-3 small" style="display:none;"></div>
                                <div class="d-flex gap-2">
                                    <button type="submit" class="btn btn-danger flex-grow-1 py-3 rounded-pill" id="reauth-confirm-btn">Confirm & Execute</button>
                                    <button type="button" class="btn btn-light px-4 rounded-pill" id="cancel-reauth-modal">Cancel</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- Work Entry Modal -->
                <div id="work-modal" class="modal-overlay" style="display:none;">
                    <div class="modal-content card shadow-lg border-0 rounded-4">
                        <div class="card-header bg-white border-bottom p-4 d-flex justify-content-between align-items-center">
                            <h5 class="fw-bolder mb-0" id="work-modal-title">Experience Details</h5>
                            <button type="button" class="btn-close" id="close-work-modal"></button>
                        </div>
                        <div class="card-body p-4">
                            <form id="workEntryForm">
                                <input type="hidden" id="w-idx" value="">
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold">Company / Organization</label>
                                        <input type="text" id="w-company" class="form-control" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-bold">Role Title</label>
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
                                        <label class="form-label small fw-bold">Job Description</label>
                                        <textarea id="w-desc" class="form-control work-desc" rows="8"></textarea>
                                    </div>
                                    <div class="col-12">
                                        <label class="form-label small fw-bold">Technologies Used (Comma separated)</label>
                                        <input type="text" id="w-skills" class="form-control" placeholder="e.g. React, Python, AWS">
                                    </div>
                                </div>
                                <div class="d-flex gap-2 mt-4">
                                    <button type="submit" class="btn btn-primary flex-grow-1" id="save-work-entry">Apply Entry</button>
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
                .modal-content { width: 95%; max-width: 820px; }
                .nav-pills .btn.active { background-color: var(--accent-sage) !important; color: #1a1918 !important; border-color: var(--accent-sage) !important; }
                .nav-pills .btn { transition: all 0.2s ease; }
                .text-justify { text-align: justify; }
                .work-desc { min-height: 180px; resize: vertical; }
                .markdown p { margin-bottom: 0.5rem; }
                .markdown ul { margin: 0; padding-left: 1.1rem; }
                .markdown ul li { margin-bottom: 0.25rem; }
            </style>`;
    },

    mount: (context) => {
        const fetchAPI = context.api;
        
        // --- Tab Switching Logic (since we don't use Bootstrap JS) ---
        const tabButtons = document.querySelectorAll('[data-bs-toggle="pill"]');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Deactivate all
                tabButtons.forEach(b => {
                    b.classList.remove('active', 'btn-primary');
                    b.classList.add('btn-outline-dark');
                    const targetId = b.getAttribute('data-bs-target');
                    document.querySelector(targetId).classList.remove('show', 'active');
                });
                // Activate clicked
                btn.classList.add('active', 'btn-primary');
                btn.classList.remove('btn-outline-dark');
                const targetId = btn.getAttribute('data-bs-target');
                document.querySelector(targetId).classList.add('show', 'active');
            });
        });

        const form = document.getElementById('profileForm');
        const workList = document.getElementById('work-history-list');
        const workModal = document.getElementById('work-modal');
        const workForm = document.getElementById('workEntryForm');
        const skillsInput = document.getElementById('p-skills');
        const skillsPreview = document.getElementById('skills-preview');
        const expError = document.getElementById('experience-error');
        const expSuccess = document.getElementById('experience-success');

        // Skills Preview Real-time update
        skillsInput.addEventListener('input', () => {
            const skills = skillsInput.value.split(',').map(s => s.trim()).filter(s => s);
            skillsPreview.innerHTML = skills.map(s => `<span class="badge bg-primary">${s}</span>`).join('');
        });

        const showExperienceError = (message) => {
            if (!expError) return;
            expError.textContent = message;
            expError.style.display = 'block';
            if (expSuccess) expSuccess.style.display = 'none';
        };

        const showExperienceSuccess = (message) => {
            if (!expSuccess) return;
            expSuccess.textContent = message;
            expSuccess.style.display = 'block';
            if (expError) expError.style.display = 'none';
        };

        const clearExperienceStatus = () => {
            if (expError) expError.style.display = 'none';
            if (expSuccess) expSuccess.style.display = 'none';
        };

        const openWorkModal = (idx = null) => {
            const titleEl = document.getElementById('work-modal-title');
            if (idx !== null) {
                titleEl.textContent = 'Edit Professional Experience';
                const item = workList.querySelector(`[data-idx="${idx}"]`);
                const data = decodeHistory(item.getAttribute('data-history'));
                if (!data) {
                    showExperienceError("Unable to load this entry. Please try again.");
                    return;
                }
                document.getElementById('w-idx').value = idx;
                document.getElementById('w-company').value = data.company;
                document.getElementById('w-role').value = data.role;
                document.getElementById('w-start').value = data.start_date;
                document.getElementById('w-end').value = data.end_date || 'Present';
                document.getElementById('w-location').value = data.location;
                document.getElementById('w-desc').value = data.description || '';
                document.getElementById('w-skills').value = (data.skills || []).join(', ');
            } else {
                titleEl.textContent = 'Add Professional Experience';
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

        workList.onclick = async (e) => {
            const item = e.target.closest('.work-list-item');
            if (!item) return;
            const idx = item.getAttribute('data-idx');

            if (e.target.closest('.remove-work-btn')) {
                if (confirm('Permanently remove this entry from your history?')) {
                    item.remove();
                    if (workList.querySelectorAll('.work-list-item').length === 0) {
                        workList.innerHTML = '<div class="p-5 text-center text-muted"><i class="bi bi-inbox display-4 d-block mb-3"></i>No history records found.</div>';
                    }
                    clearExperienceStatus();
                    await submitExperience();
                }
            } else if (e.target.closest('.edit-work-btn')) {
                openWorkModal(idx);
            }
        };

        workForm.onsubmit = async (e) => {
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
                <div class="list-group-item p-4 work-list-item border rounded-3 bg-white shadow-sm mb-3" data-idx="${idx || Date.now()}" data-history="${encodeHistory(entry)}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <h5 class="fw-bold mb-0">${entry.role}</h5>
                                <span class="badge bg-light text-dark border small">${entry.end_date === 'Present' ? 'Current' : 'Past'}</span>
                            </div>
                            <div class="text-primary fw-bold mb-2"><i class="bi bi-building mr-1"></i> ${entry.company}</div>
                            <div class="text-muted small mb-3">
                                <i class="bi bi-calendar3 mr-1"></i> <span>${entry.start_date}</span> &ndash; <span>${entry.end_date || "Present"}</span>
                                <span class="ms-3"><i class="bi bi-geo-alt mr-1"></i> ${entry.location}</span>
                            </div>
                            <div class="mb-0 small text-muted text-justify markdown" style="max-width: 800px;">${renderMarkdown(entry.description || "")}</div>
                        </div>
                        <div class="btn-group ms-3">
                            <button type="button" class="btn btn-sm btn-outline-secondary edit-work-btn" title="Edit"><i class="bi bi-pencil"></i></button>
                            <button type="button" class="btn btn-sm btn-outline-danger remove-work-btn" title="Delete"><i class="bi bi-trash"></i></button>
                        </div>
                    </div>
                </div>`;

            if (idx !== "") {
                const oldItem = workList.querySelector(`[data-idx="${idx}"]`);
                oldItem.outerHTML = html;
            } else {
                const emptyMsg = workList.querySelector('.text-muted.p-5');
                if (emptyMsg) workList.innerHTML = '';
                workList.insertAdjacentHTML('afterbegin', html); // Add newest to top
            }
            closeWorkModal();
            clearExperienceStatus();
            await submitExperience();
        };

        const uploadBtn = document.getElementById('p-image-upload-btn');
        const fileInput = document.getElementById('p-image-file');
        const urlInput = document.getElementById('p-image');
        const previewImg = document.getElementById('p-image-preview');

        if (uploadBtn && fileInput) {
            uploadBtn.onclick = () => fileInput.click();
            fileInput.onchange = async () => {
                if (fileInput.files.length === 0) return;
                
                const file = fileInput.files[0];
                const formData = new FormData();
                formData.append('file', file);

                uploadBtn.disabled = true;
                uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

                try {
                    const result = await fetchAPI('/api/content/profile/photo', {
                        method: 'POST',
                        body: formData
                    });

                    urlInput.value = result.url;
                    previewImg.src = result.url;
                    alert('Profile photo updated successfully!');
                } catch (err) {
                    alert('Upload failed: ' + err.message);
                } finally {
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = '<i class="bi bi-cloud-upload mr-2"></i> Upload';
                }
            };
        }

        const gatherProfileData = () => {
            const social_links = {};
            Object.keys(socialIconMap).forEach(key => {
                const val = document.getElementById(`social-${key}`).value;
                if (val) social_links[key] = val;
            });

            const work_history = Array.from(workList.querySelectorAll('.work-list-item')).map(item => {
                const decoded = decodeHistory(item.getAttribute('data-history'));
                return decoded;
            }).filter(item => item);

            return {
                name: document.getElementById('p-name').value,
                location: document.getElementById('p-location').value,
                headline_role: document.getElementById('p-headline').value,
                statement: document.getElementById('p-statement').value,
                image_url: document.getElementById('p-image').value,
                skills: document.getElementById('p-skills').value.split(',').map(s => s.trim()).filter(s => s),
                social_links,
                work_history
            };
        };

        const submitProfile = async (data) => {
            try {
                await fetchAPI('/api/content/profile', {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
                alert('Profile updated successfully!');
                context.navigate('/home');
            } catch (err) {
                const errEl = document.getElementById('profile-error');
                errEl.textContent = "Save failed: " + err.message;
                errEl.style.display = 'block';
                window.scrollTo(0, 0);
            }
        };

        const submitExperience = async () => {
            try {
                await fetchAPI('/api/content/profile', {
                    method: 'PUT',
                    body: JSON.stringify(gatherProfileData())
                });
                showExperienceSuccess('Experience updated successfully.');
            } catch (err) {
                showExperienceError("Save failed: " + err.message);
            }
        };

        form.onsubmit = (e) => {
            e.preventDefault();
            submitProfile(gatherProfileData());
        };

        // --- Security / Password Change ---
        const passwordForm = document.getElementById('changePasswordForm');
        passwordForm.onsubmit = async (e) => {
            e.preventDefault();
            const current_password = document.getElementById('current-password').value;
            const new_password = document.getElementById('new-password').value;
            const confirm_password = document.getElementById('confirm-password').value;
            const errorEl = document.getElementById('password-error');
            const successEl = document.getElementById('password-success');

            errorEl.style.display = 'none';
            successEl.style.display = 'none';

            if (new_password !== confirm_password) {
                errorEl.textContent = "New passwords do not match.";
                errorEl.style.display = 'block';
                return;
            }

            try {
                await fetchAPI('/api/auth/change-password', {
                    method: 'POST',
                    body: JSON.stringify({ current_password, new_password })
                });
                successEl.style.display = 'block';
                passwordForm.reset();
            } catch (err) {
                errorEl.textContent = err.message;
                errorEl.style.display = 'block';
            }
        };

        // --- Re-authentication & Advanced Security Actions ---
        const reauthModal = document.getElementById('reauth-modal');
        const reauthForm = document.getElementById('reauthForm');
        const reauthError = document.getElementById('reauth-error');
        const changeEmailForm = document.getElementById('changeEmailForm');
        const deleteAccountBtn = document.getElementById('delete-account-btn');
        
        let reauthContext = null; // 'email' or 'delete'

        const openReauthModal = (context) => {
            reauthContext = context;
            const titleEl = document.getElementById('reauth-modal-title');
            const messageEl = document.getElementById('reauth-message');
            const confirmBtn = document.getElementById('reauth-confirm-btn');

            if (context === 'delete') {
                titleEl.textContent = 'Permanently Delete Account?';
                messageEl.innerHTML = '<strong class="text-danger">Warning:</strong> This will delete your profile, work history, and all comments. This cannot be undone.';
                confirmBtn.className = 'btn btn-danger flex-grow-1 py-3 rounded-pill';
                confirmBtn.textContent = 'Confirm Permanent Deletion';
            } else {
                titleEl.textContent = 'Confirm Email Change';
                messageEl.textContent = 'Please enter your password to authorize updating your account email address.';
                confirmBtn.className = 'btn btn-dark flex-grow-1 py-3 rounded-pill';
                confirmBtn.textContent = 'Authorize Update';
            }

            reauthError.style.display = 'none';
            reauthForm.reset();
            reauthModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        };

        const closeReauthModal = () => {
            reauthModal.style.display = 'none';
            document.body.style.overflow = '';
            reauthContext = null;
        };

        document.getElementById('close-reauth-modal').onclick = closeReauthModal;
        document.getElementById('cancel-reauth-modal').onclick = closeReauthModal;

        changeEmailForm.onsubmit = (e) => {
            e.preventDefault();
            document.getElementById('email-error').style.display = 'none';
            document.getElementById('email-success').style.display = 'none';
            openReauthModal('email');
        };

        deleteAccountBtn.onclick = () => {
            openReauthModal('delete');
        };

        reauthForm.onsubmit = async (e) => {
            e.preventDefault();
            const password = document.getElementById('reauth-password').value;
            reauthError.style.display = 'none';

            try {
                if (reauthContext === 'email') {
                    const newEmail = document.getElementById('new-email').value;
                    await fetchAPI('/api/auth/change-email', {
                        method: 'POST',
                        body: JSON.stringify({ current_password: password, new_email: newEmail })
                    });
                    document.getElementById('email-success').style.display = 'block';
                    // Optional: Update local user object if stored in memory
                    closeReauthModal();
                } else if (reauthContext === 'delete') {
                    await fetchAPI('/api/auth/delete-account', {
                        method: 'POST',
                        body: JSON.stringify({ current_password: password })
                    });
                    // Success means we are logged out and account is gone
                    alert('Your account has been permanently deleted. Goodbye.');
                    window.location.href = '/';
                }
            } catch (err) {
                reauthError.textContent = err.message;
                reauthError.style.display = 'block';
            }
        };
    }
};
