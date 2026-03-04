/**
 * ProfileView.js
 * Manages the developer profile edit view with structured fields for social links and work history.
 */

export const ProfileView = {
    /**
     * Template for the Profile Edit form.
     */
    template: (d) => `
        <section id="view-admin-profile" class="py-5" data-test="view-admin-profile">
            <div class="container px-5">
                <div class="bg-light rounded-4 py-5 px-4 px-md-5">
                    <div class="text-center mb-5">
                        <div class="feature bg-primary bg-gradient-primary-to-secondary text-white rounded-3 mb-3"><i class="bi bi-person-badge"></i></div>
                        <h1 class="fw-bolder">Edit Profile</h1>
                        <p class="lead fw-normal text-muted mb-0">Update your developer identity</p>
                    </div>
                    <div class="row gx-5 justify-content-center">
                        <div class="col-lg-10 col-xl-8">
                            <form id="profileForm">
                                <div id="profile-error" class="alert alert-danger" style="display:none;"></div>
                                
                                <div class="mb-4">
                                    <h5 class="fw-bolder mb-3">Core Identity</h5>
                                    <div class="mb-3">
                                        <label class="form-label">Profile Photo</label>
                                        <div class="d-flex align-items-center gap-3 mb-2">
                                            <div id="image-preview">
                                                ${d.image_url ? `<img src="${d.image_url}" class="rounded-circle" style="width:80px;height:80px;object-fit:cover;">` : '<div class="bg-secondary rounded-circle" style="width:80px;height:80px;"></div>'}
                                            </div>
                                            <input type="file" id="p-file" class="form-control form-control-sm" accept="image/*">
                                            <button type="button" class="btn btn-sm btn-outline-info" id="p-upload">Replace Photo</button>
                                        </div>
                                        <input type="hidden" id="p-img-url" value="${d.image_url || ''}">
                                    </div>

                                    <div class="form-floating mb-3">
                                        <input class="form-control" id="p-name" type="text" value="${d.name}" required />
                                        <label for="p-name">Full name</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <input class="form-control" id="p-loc" type="text" value="${d.location}" required />
                                        <label for="p-loc">Location</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <textarea class="form-control" id="p-stmt" style="height: 10rem" required>${d.statement}</textarea>
                                        <label for="p-stmt">Professional Statement</label>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Skills (comma separated)</label>
                                        <input class="form-control" id="p-skills" type="text" value="${d.skills.join(', ')}" />
                                    </div>
                                </div>

                                <div class="mb-4">
                                    <h5 class="fw-bolder mb-3">Social Media Links</h5>
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label small">GitHub URL</label>
                                            <input type="url" class="form-control form-control-sm p-soc-input" data-platform="github" value="${d.social_links.github || ''}" placeholder="https://github.com/username">
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label small">LinkedIn URL</label>
                                            <input type="url" class="form-control form-control-sm p-soc-input" data-platform="linkedin" value="${d.social_links.linkedin || ''}" placeholder="https://linkedin.com/in/username">
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label small">Twitter URL</label>
                                            <input type="url" class="form-control form-control-sm p-soc-input" data-platform="twitter" value="${d.social_links.twitter || ''}" placeholder="https://twitter.com/username">
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label small">LeetCode URL</label>
                                            <input type="url" class="form-control form-control-sm p-soc-input" data-platform="leetcode" value="${d.social_links.leetcode || ''}" placeholder="https://leetcode.com/username">
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label small">Kaggle URL</label>
                                            <input type="url" class="form-control form-control-sm p-soc-input" data-platform="kaggle" value="${d.social_links.kaggle || ''}" placeholder="https://kaggle.com/username">
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label class="form-label small">HackTheBox URL</label>
                                            <input type="url" class="form-control form-control-sm p-soc-input" data-platform="hackthebox" value="${d.social_links.hackthebox || ''}" placeholder="https://app.hackthebox.com/profile/username">
                                        </div>
                                    </div>
                                </div>

                                <div class="mb-4">
                                    <div class="d-flex justify-content-between align-items-center mb-3">
                                        <h5 class="fw-bolder mb-0">Work History</h5>
                                        <button type="button" class="btn btn-sm btn-primary" id="add-work-btn"><i class="bi bi-plus-circle me-1"></i>Add Entry</button>
                                    </div>
                                    <div id="work-history-container">
                                        ${d.work_history.map((item, index) => ProfileView.workEntryTemplate(item, index)).join('')}
                                    </div>
                                </div>

                                <button type="submit" class="btn btn-success btn-lg w-100 mt-4">Save All Changes</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </section>`,

    /**
     * Template for a single work history entry.
     */
    workEntryTemplate: (item = {}, index = Date.now()) => `
        <div class="card mb-3 work-entry shadow-sm border-0 bg-white" data-index="${index}">
            <div class="card-body p-3">
                <div class="d-flex justify-content-between mb-2">
                    <h6 class="fw-bold mb-0">Experience Entry</h6>
                    <button type="button" class="btn-close remove-work-btn" aria-label="Remove"></button>
                </div>
                <div class="row g-2">
                    <div class="col-md-6">
                        <input type="text" class="form-control form-control-sm mb-2 w-company" placeholder="Company Name" value="${item.company || ''}" required>
                    </div>
                    <div class="col-md-6">
                        <input type="text" class="form-control form-control-sm mb-2 w-role" placeholder="Job Role" value="${item.role || ''}" required>
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control form-control-sm mb-2 w-start" placeholder="Start (e.g. 2021-01)" value="${item.start_date || ''}" required>
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control form-control-sm mb-2 w-end" placeholder="End (e.g. Present)" value="${item.end_date || 'Present'}">
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control form-control-sm mb-2 w-location" placeholder="Location" value="${item.location || ''}" required>
                    </div>
                    <div class="col-12">
                        <textarea class="form-control form-control-sm mb-2 w-desc" placeholder="Responsibilities & Achievements" rows="2">${item.description || ''}</textarea>
                    </div>
                    <div class="col-12">
                        <input type="text" class="form-control form-control-sm w-skills" placeholder="Key Skills (comma separated)" value="${(item.skills || []).join(', ')}">
                    </div>
                </div>
            </div>
        </div>`,

    /**
     * Binds event listeners for the profile view.
     */
    bindEvents: (fetchAPI, router) => {
        const uploadBtn = document.getElementById('p-upload');
        const form = document.getElementById('profileForm');
        const addWorkBtn = document.getElementById('add-work-btn');
        const workContainer = document.getElementById('work-history-container');

        // Photo Upload
        uploadBtn.addEventListener('click', async () => {
            const fileInput = document.getElementById('p-file');
            if (!fileInput.files.length) return;
            const fd = new FormData();
            fd.append('file', fileInput.files[0]);
            try {
                const res = await fetchAPI('/api/content/profile/photo', { method: 'POST', body: fd });
                document.getElementById('p-img-url').value = res.url;
                document.getElementById('image-preview').innerHTML = `<img src="${res.url}" class="rounded-circle" style="width:80px;height:80px;object-fit:cover;">`;
                alert(res.message);
            } catch (err) { alert("Upload failed: " + err.message); }
        });

        // Add Work History Entry
        addWorkBtn.addEventListener('click', () => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = ProfileView.workEntryTemplate();
            workContainer.appendChild(tempDiv.firstElementChild);
        });

        // Remove Work History Entry (Event Delegation)
        workContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-work-btn')) {
                e.target.closest('.work-entry').remove();
            }
        });

        // Form Submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                // Collect Social Links
                const social_links = {};
                document.querySelectorAll('.p-soc-input').forEach(input => {
                    const val = input.value.trim();
                    if (val) social_links[input.dataset.platform] = val;
                });

                // Collect Work History
                const work_history = Array.from(document.querySelectorAll('.work-entry')).map(card => ({
                    company: card.querySelector('.w-company').value.trim(),
                    role: card.querySelector('.w-role').value.trim(),
                    start_date: card.querySelector('.w-start').value.trim(),
                    end_date: card.querySelector('.w-end').value.trim(),
                    location: card.querySelector('.w-location').value.trim(),
                    description: card.querySelector('.w-desc').value.trim(),
                    skills: card.querySelector('.w-skills').value.split(',').map(s=>s.trim()).filter(s=>s)
                }));

                const body = {
                    name: document.getElementById('p-name').value.trim(),
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
                window.location.hash = '#home';
            } catch (err) {
                const errEl = document.getElementById('profile-error');
                errEl.textContent = "Save failed: " + err.message;
                errEl.style.display = 'block';
                window.scrollTo(0, 0);
            }
        });
    }
};
