const iconMap = {
    github: "bi-github",
    linkedin: "bi-linkedin",
    twitter: "bi-twitter",
    tiktok: "bi-tiktok",
    leetcode: "bi-code-slash",
    kaggle: "bi-graph-up",
    hackthebox: "bi-box-seam",
};

function renderSocialLinks(links = {}) {
    return Object.entries(links)
        .filter(([, url]) => typeof url === "string" && url.trim())
        .map(([key, url]) => {
            const icon = iconMap[key] || "bi-link-45deg";
            return `
                <a class="text-gradient" href="${url}" target="_blank" rel="noopener" data-test="social-link-${key}">
                    <i class="bi ${icon}"></i>
                </a>`;
        })
        .join("");
}

export const HomeView = {
    template(profile) {
        const data = profile || {};
        const workItems = Array.isArray(data.work_history) ? data.work_history : [];
        return `
            <section id="view-home" class="py-5" data-test="view-home">
                <header class="py-5">
                    <div class="container px-5 pb-5">
                        <div class="row gx-5 align-items-center">
                            <div class="col-xxl-5">
                                <div class="text-center text-xxl-start">
                                    <div class="badge bg-gradient-primary-to-secondary text-white mb-4">
                                        <div class="text-uppercase">${data.location || ""}</div>
                                    </div>
                                    <h1 class="display-3 fw-bolder mb-5">
                                        <span class="text-gradient d-inline" data-test="profile-name">${data.name || ""}</span>
                                    </h1>
                                    <div class="fs-3 fw-light text-muted mb-5" data-test="profile-statement">${data.statement || ""}</div>
                                    <div class="d-flex justify-content-center justify-content-xxl-start gap-3 fs-2 mb-5" data-test="profile-socials">
                                        ${renderSocialLinks(data.social_links || {})}
                                    </div>
                                </div>
                            </div>
                            <div class="col-xxl-7">
                                <div class="d-flex justify-content-center mt-5 mt-xxl-0">
                                    <div class="profile bg-gradient-primary-to-secondary">
                                        ${data.image_url ? `<img class="profile-img" src="${data.image_url}" alt="Profile image" data-test="profile-image" />` : ""}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </header>

                <section class="py-5 bg-light" aria-label="Experience">
                    <div class="container px-5">
                        <div class="row gx-5 justify-content-center">
                            <div class="col-xxl-8">
                                <div class="text-center mb-5">
                                    <h2 class="display-5 fw-bolder">
                                        <span class="text-gradient d-inline">Experience</span>
                                    </h2>
                                </div>
                                ${workItems
                                    .map((w, idx) => `
                                        <article class="card shadow border-0 rounded-4 mb-5" data-test="work-card-${idx}">
                                            <div class="card-body p-5">
                                                <div class="row align-items-center gx-5">
                                                    <div class="col text-center text-lg-start mb-4 mb-lg-0">
                                                        <div class="bg-light p-4 rounded-4">
                                                            <div class="text-primary fw-bolder mb-2">${w.start_date || ""} - ${w.end_date || ""}</div>
                                                            <div class="small fw-bolder">${w.role || ""}</div>
                                                            <div class="small text-muted">${w.company || ""}</div>
                                                            <div class="small text-muted">${w.location || ""}</div>
                                                        </div>
                                                    </div>
                                                    <div class="col-lg-8">
                                                        <div>${w.description || ""}</div>
                                                        <div class="mt-3">
                                                            ${(w.skills || []).map(s => `<span class="badge bg-secondary me-1">${s}</span>`).join("")}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </article>
                                    `)
                                    .join("")}
                            </div>
                        </div>
                    </div>
                </section>
            </section>`;
    },
};
