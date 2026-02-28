/**
 * ProfileView.js
 * Manages the developer profile edit view and its singleton asset logic.
 */

export const ProfileView = {
    /**
     * Template for the Profile Edit form.
     */
    template: (d) => `
        <section class="py-5">
            <div class="container px-5">
                <div class="bg-light rounded-4 py-5 px-4 px-md-5">
                    <div class="text-center mb-5">
                        <div class="feature bg-primary bg-gradient-primary-to-secondary text-white rounded-3 mb-3"><i class="bi bi-person-badge"></i></div>
                        <h1 class="fw-bolder">Edit Profile</h1>
                        <p class="lead fw-normal text-muted mb-0">Update your developer identity</p>
                    </div>
                    <div class="row gx-5 justify-content-center">
                        <div class="col-lg-8 col-xl-6">
                            <form id="profileForm">
                                <div id="profile-error" class="alert alert-danger" style="display:none;"></div>
                                
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
                                    <small class="text-muted">Uploading a new photo immediately replaces the current one.</small>
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
                                <div class="mb-3">
                                    <label class="small text-muted">Social Links (JSON)</label>
                                    <textarea id="p-soc" class="form-control mb-2 font-monospace">${JSON.stringify(d.social_links, null, 2)}</textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="small text-muted">Work History (JSON)</label>
                                    <textarea id="p-work" class="form-control mb-2 font-monospace">${JSON.stringify(d.work_history, null, 2)}</textarea>
                                </div>
                                <button type="submit" class="btn btn-success btn-lg w-100">Save All Changes</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </section>`,

    /**
     * Binds event listeners for the profile view.
     */
    bindEvents: (fetchAPI, router) => {
        const uploadBtn = document.getElementById('p-upload');
        const form = document.getElementById('profileForm');

        // Specialized Singleton Photo Upload
        uploadBtn.addEventListener('click', async () => {
            const fileInput = document.getElementById('p-file');
            if (!fileInput.files.length) return;
            
            const fd = new FormData();
            fd.append('file', fileInput.files[0]);
            
            try {
                // Use the specialized singleton endpoint
                const res = await fetchAPI('/api/content/profile/photo', { method: 'POST', body: fd });
                document.getElementById('p-img-url').value = res.url;
                document.getElementById('image-preview').innerHTML = `<img src="${res.url}" class="rounded-circle" style="width:80px;height:80px;object-fit:cover;">`;
                alert(res.message);
            } catch (err) {
                alert("Upload failed: " + err.message);
            }
        });

        // Profile Form Submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const body = {
                    name: document.getElementById('p-name').value,
                    location: document.getElementById('p-loc').value,
                    statement: document.getElementById('p-stmt').value,
                    image_url: document.getElementById('p-img-url').value,
                    skills: document.getElementById('p-skills').value.split(',').map(s=>s.trim()).filter(s=>s),
                    social_links: JSON.parse(document.getElementById('p-soc').value),
                    work_history: JSON.parse(document.getElementById('p-work').value),
                    interests: [] // Default for now
                };
                await fetchAPI('/api/content/profile', { method: 'PUT', body: JSON.stringify(body) });
                alert("Profile and metadata saved successfully!");
                window.location.hash = '#home';
            } catch (err) {
                const errEl = document.getElementById('profile-error');
                errEl.textContent = "Save failed: " + err.message;
                errEl.style.display = 'block';
            }
        });
    }
};
