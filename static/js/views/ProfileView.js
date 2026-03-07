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

export const ProfileView = {
    /**
     * Helper to sort work history chronologically (Present/Newest at top)
     */
    sortWorkHistory: (history) => {
        return [...history].sort((a, b) => {
            const dateA = a.end_date === "Present" ? new Date() : new Date(a.end_date || a.start_date);
            const dateB = b.end_date === "Present" ? new Date() : new Date(b.end_date || b.start_date);
            return dateB - dateA;
        });
    },

    /**
     * Template for the Profile Edit form.
     */
    template: (d) => {
        const sortedHistory = ProfileView.sortWorkHistory(d.work_history || []);
        return `
        <section id="view-admin-profile" class="py-5" data-test="view-admin-profile">
            <div class="container px-5">
                <div class="bg-light rounded-4 py-5 px-4 px-md-5">
                    <div class="text-center mb-5">
                        <div class="feature bg-primary text-white rounded-3 mb-3">Profile</div>
                        <h1 class="fw-bolder">Edit Profile</h1>
                        <p class="lead fw-normal text-muted mb-0">Update your developer identity</p>
                    </div>
                    <div class="row gx-5 justify-content-center">
                        <div class="col-lg-10 col-xl-8">
                            <form id="profileForm">
                                <div id="profile-error" class="alert alert-danger" style="display:none;"></div>
                                
                                <div class="mb-5 shadow-sm p-4 bg-white rounded-4">
                                    <h5 class="fw-bolder mb-4 pb-2 border-bottom">Core Identity</h5>
                                    <div class="mb-4">
                                        <label class="form-label text-muted small fw-bold text-uppercase">Profile Photo</label>
                                        <div class="d-flex align-items-center gap-4 p-3 bg-light rounded-3">
                                            <div id="image-preview" class="shadow-sm">
                                                ${d.image_url ? `<img src="${d.image_url}" class="rounded-circle border border-2 border-white" style="width:80px;height:80px;object-fit:cover;">` : '<div class="bg-secondary rounded-circle" style="width:80px;height:80px;"></div>'}
                                            </div>
                                            <div class="flex-grow-1">
                                                <input type="file" id="p-file" class="form-control form-control-sm mb-2" accept="image/*">
                                                <button type="button" class="btn btn-sm btn-outline-primary" id="p-upload">Upload New Photo</button>
                                            </div>
                                        </div>
                                        <input type="hidden" id="p-img-url" value="${d.image_url || ''}">
                                    </div>

                                    <div class="form-floating mb-3">
                                        <input class="form-control" id="p-name" type="text" value="${d.name}" placeholder="Name" required />
                                        <label for="p-name">Full name</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <input class="form-control" id="p-headline" type="text" value="${d.headline_role || ''}" placeholder="Headline Role" />
                                        <label for="p-headline">Headline Role (Optional)</label>
                                        <div class="form-text text-muted small px-2">
                                            This will be shown on the hero card. <strong>Note:</strong> Any work experience marked as 'Present' will override this.
                                        </div>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <input class="form-control" id="p-loc" type="text" value="${d.location}" placeholder="Location" required />
                                        <label for="p-loc">Location</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <textarea class="form-control" id="p-stmt" style="height: 10rem" placeholder="Statement" required>${d.statement}</textarea>
                                        <label for="p-stmt">Professional Statement</label>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-muted small fw-bold text-uppercase">Skills (comma separated)</label>
                                        <input class="form-control" id="p-skills" type="text" value="${d.skills.join(', ')}" placeholder="Python, React, etc." />
                                    </div>
                                </div>

                                <div class="mb-5 shadow-sm p-4 bg-white rounded-4">
                                    <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom">
                                        <h5 class="fw-bolder mb-0">Social Media Links</h5>
                                        <button type="button" class="btn btn-sm btn-outline-primary" id="add-social-link">+ Add Link</button>
                                    </div>
                                    <div class="row g-3" id="social-links-container">
                                        ${ProfileView.socialLinkTemplateList(d.social_links)}
                                    </div>
                                </div>

                                <div class="mb-5 shadow-sm p-4 bg-white rounded-4">
                                    <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom">
                                        <h5 class="fw-bolder mb-0">Work History</h5>
                                        <button type="button" class="btn btn-sm btn-primary" id="open-add-work-modal">+ Add Experience</button>
                                    </div>
                                    
                                    <div id="work-history-list" class="mb-3">
                                        ${sortedHistory.length ? sortedHistory.map((item, index) => ProfileView.workListEntryTemplate(item, index)).join('') : '<p class="text-center text-muted py-3">No work history added yet.</p>'}
                                    </div>
                                </div>

                                <button type="submit" class="btn btn-success btn-lg w-100 mt-4 shadow-sm">Save Complete Profile</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Experience Form Modal (Overlay) -->
            <div id="work-modal" class="modal-overlay" style="display:none;">
                <div class="modal-content card shadow-lg border-0 rounded-4">
                    <div class="card-header bg-white border-bottom p-4 d-flex justify-content-between align-items-center">
                        <h5 class="fw-bolder mb-0" id="work-modal-title">Add Work Experience</h5>
                        <button type="button" class="btn-close" id="close-work-modal"></button>
                    </div>
                    <div class="card-body p-4">
                        <form id="workEntryForm">
                            <input type="hidden" id="w-edit-index" value="">
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <label class="form-label small fw-bold">Company</label>
                                    <input type="text" id="w-company" class="form-control" placeholder="e.g. Acme Corp" required>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label small fw-bold">Role</label>
                                    <input type="text" id="w-role" class="form-control" placeholder="e.g. Senior Developer" required>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label small fw-bold">Start Date</label>
                                    <input type="text" id="w-start" class="form-control" placeholder="YYYY-MM" required>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label small fw-bold">End Date</label>
                                    <input type="text" id="w-end" class="form-control" placeholder="YYYY-MM or Present" value="Present">
                                </div>
                                <div class="col-12">
                                    <label class="form-label small fw-bold">Location</label>
                                    <input type="text" id="w-location" class="form-control" placeholder="City, Country" required>
                                </div>
                                <div class="col-12">
                                    <label class="form-label small fw-bold">Description</label>
                                    <textarea id="w-desc" class="form-control" rows="3" placeholder="Achievements..."></textarea>
                                </div>
                                <div class="col-12">
                                    <label class="form-label small fw-bold">Key Skills (comma separated)</label>
                                    <input type="text" id="w-skills" class="form-control" placeholder="Python, Docker, etc.">
                                </div>
                            </div>
                            <div class="d-flex gap-2 mt-4">
                                <button type="button" class="btn btn-primary flex-grow-1" id="save-work-entry">Update List</button>
                                <button type="button" class="btn btn-light" id="cancel-work-modal">Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </section>
        <style>
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(30, 30, 30, 0.6);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                backdrop-filter: blur(4px);
            }
            .modal-content {
                width: 95%;
                max-width: 600px;
                max-height: 90vh;
                overflow-y: auto;
            }
            .work-list-item {
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                border-left: 4px solid var(--accent-sage);
            }
            .work-list-item:hover {
                background-color: #f8f9fa !important;
            }
            .social-link-row input:focus {
                z-index: 1;
            }
        </style>`;
    },

    /**
     * Template for a single work item in the list view (with edit/delete buttons).
     */
    workListEntryTemplate: (item, index) => `
        <div class="work-list-item card mb-3 bg-white border border-light shadow-sm" data-index="${index}">
            <div class="card-body p-4 d-flex justify-content-between align-items-center">
                <div class="flex-grow-1">
                    <h5 class="fw-bolder mb-1" style="color: var(--text);">${item.role}</h5>
                    <div class="text-primary fw-bold mb-2">${item.company}</div>
                    <div class="text-muted d-flex gap-3 small">
                        <span>📅 ${item.start_date} — ${item.end_date}</span>
                        <span>📍 ${item.location}</span>
                    </div>
                </div>
                <div class="d-flex gap-2 ms-3">
                    <button type="button" class="btn btn-outline-primary edit-work-btn px-3" data-index="${index}">Edit</button>
                    <button type="button" class="btn btn-outline-danger remove-work-btn px-3" data-index="${index}">Delete</button>
                </div>
            </div>
            <!-- Hidden inputs for form data collection -->
            <input type="hidden" class="w-data" value='${JSON.stringify(item).replace(/'/g, "&apos;")}'>
        </div>`,

    socialLinkTemplate: (platform = "", url = "") => `
        <div class="col-md-6 social-link-row">
            <div class="d-flex align-items-center gap-2">
                <input type="text" class="form-control form-control-sm p-soc-key" placeholder="platform" value="${platform}">
                <input type="url" class="form-control form-control-sm p-soc-input" placeholder="URL" value="${url}">
                <button type="button" class="btn btn-sm btn-outline-danger remove-social-link" title="Remove link">&times;</button>
            </div>
        </div>`,

    socialLinkTemplateList: (links = {}) => {
        const entries = Object.entries(links || {});
        if (!entries.length) return ProfileView.socialLinkTemplate();
        return entries
            .map(([platform, url]) => ProfileView.socialLinkTemplate(platform, url))
            .join('');
    },

    /**
     * Binds event listeners for the profile view.
     */
    mount: (context) => {
        console.log("ProfileView Mount Called");
        const fetchAPI = context.api;
        const form = document.getElementById('profileForm');
        if (!form) {
            console.error("Profile form not found in DOM!");
            return;
        }
        const uploadBtn = document.getElementById('p-upload');
        const addSocialBtn = document.getElementById('add-social-link');
        const socialContainer = document.getElementById('social-links-container');
        
        // Work History State Elements
        const workList = document.getElementById('work-history-list');
        const workModal = document.getElementById('work-modal');
        const openAddWorkBtn = document.getElementById('open-add-work-modal');
        const closeWorkModalBtn = document.getElementById('close-work-modal');
        const cancelWorkModalBtn = document.getElementById('cancel-work-modal');
        const saveWorkEntryBtn = document.getElementById('save-work-entry');
        const workEntryForm = document.getElementById('workEntryForm');

        // Modal Helpers
        const openModal = (item = null, index = null) => {
            const title = document.getElementById('work-modal-title');
            const editIdx = document.getElementById('w-edit-index');
            
            if (item) {
                title.textContent = "Edit Experience";
                editIdx.value = index;
                document.getElementById('w-company').value = item.company || '';
                document.getElementById('w-role').value = item.role || '';
                document.getElementById('w-start').value = item.start_date || '';
                document.getElementById('w-end').value = item.end_date || 'Present';
                document.getElementById('w-location').value = item.location || '';
                document.getElementById('w-desc').value = item.description || '';
                document.getElementById('w-skills').value = (item.skills || []).join(', ');
            } else {
                title.textContent = "Add Work Experience";
                editIdx.value = '';
                workEntryForm.reset();
                document.getElementById('w-end').value = 'Present';
            }
            workModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        };

        const closeModal = () => {
            workModal.style.display = 'none';
            document.body.style.overflow = '';
        };

        // Work History Listeners
        openAddWorkBtn.addEventListener('click', () => openModal());
        closeWorkModalBtn.addEventListener('click', closeModal);
        cancelWorkModalBtn.addEventListener('click', closeModal);

        workList.addEventListener('click', (e) => {
            const index = e.target.getAttribute('data-index');
            if (e.target.classList.contains('edit-work-btn')) {
                const row = e.target.closest('.work-list-item');
                const data = JSON.parse(row.querySelector('.w-data').value);
                openModal(data, index);
            } else if (e.target.classList.contains('remove-work-btn')) {
                if (confirm("Delete this experience entry?")) {
                    e.target.closest('.work-list-item').remove();
                }
            }
        });

        saveWorkEntryBtn.addEventListener('click', () => {
            const editIdx = document.getElementById('w-edit-index').value;
            const item = {
                company: document.getElementById('w-company').value.trim(),
                role: document.getElementById('w-role').value.trim(),
                start_date: document.getElementById('w-start').value.trim(),
                end_date: document.getElementById('w-end').value.trim(),
                location: document.getElementById('w-location').value.trim(),
                description: document.getElementById('w-desc').value.trim(),
                skills: document.getElementById('w-skills').value.split(',').map(s=>s.trim()).filter(s=>s)
            };

            if (!item.company || !item.role || !item.start_date) {
                alert("Please fill in required fields (Company, Role, Start Date)");
                return;
            }

            if (editIdx !== "") {
                const oldRow = workList.querySelector(`.work-list-item[data-index="${editIdx}"]`);
                oldRow.outerHTML = ProfileView.workListEntryTemplate(item, editIdx);
            } else {
                const newIdx = Date.now();
                const temp = document.createElement('div');
                temp.innerHTML = ProfileView.workListEntryTemplate(item, newIdx);
                workList.appendChild(temp.firstElementChild);
            }
            
            // Re-sort the view locally or just wait for save. 
            // Better to re-render the whole list to maintain chronological order immediately
            const currentHistory = Array.from(workList.querySelectorAll('.w-data')).map(i => JSON.parse(i.value));
            const sorted = ProfileView.sortWorkHistory(currentHistory);
            workList.innerHTML = sorted.map((it, idx) => ProfileView.workListEntryTemplate(it, idx)).join('');
            
            closeModal();
        });

        // Photo Upload
        uploadBtn.addEventListener('click', async () => {
            const fileInput = document.getElementById('p-file');
            if (!fileInput.files.length) return;
            const fd = new FormData();
            fd.append('file', fileInput.files[0]);
            try {
                const res = await fetchAPI('/api/content/profile/photo', { method: 'POST', body: fd });
                document.getElementById('p-img-url').value = res.url;
                document.getElementById('image-preview').innerHTML = `<img src="${res.url}" class="rounded-circle border border-2 border-white" style="width:80px;height:80px;object-fit:cover;">`;
                alert(res.message);
            } catch (err) { alert("Upload failed: " + err.message); }
        }, { signal: context.signal });

        addSocialBtn.addEventListener('click', () => {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = ProfileView.socialLinkTemplate();
            socialContainer.appendChild(wrapper.firstElementChild);
        }, { signal: context.signal });

        socialContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-social-link')) {
                e.target.closest('.social-link-row').remove();
            }
        }, { signal: context.signal });

        // Form Submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const social_links = {};
                document.querySelectorAll('.social-link-row').forEach(row => {
                    const key = row.querySelector('.p-soc-key').value.trim();
                    const val = row.querySelector('.p-soc-input').value.trim();
                    if (key && val) social_links[key] = val;
                });

                const work_history = Array.from(workList.querySelectorAll('.w-data')).map(el => JSON.parse(el.value));

                const body = {
                    name: document.getElementById('p-name').value.trim(),
                    headline_role: document.getElementById('p-headline').value.trim(),
                    location: document.getElementById('p-loc').value.trim(),
                    statement: document.getElementById('p-stmt').value.trim(),
                    image_url: document.getElementById('p-img-url').value,
                    skills: document.getElementById('p-skills').value.split(',').map(s=>s.trim()).filter(s=>s),
                    social_links: social_links,
                    work_history: work_history,
                    interests: []
                };

                await fetchAPI('/api/content/profile', { method: 'PUT', body: JSON.stringify(body) });
                alert("Profile saved successfully!");
                context.navigate('#home');
            } catch (err) {
                const errEl = document.getElementById('profile-error');
                errEl.textContent = "Save failed: " + err.message;
                errEl.style.display = 'block';
                window.scrollTo(0, 0);
            }
        }, { signal: context.signal });
    }
};
