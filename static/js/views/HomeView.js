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
    return Object.entries(links)
        .filter(([, url]) => typeof url === "string" && url.trim())
        .map(([key, url]) => {
            const label = key.replace(/[-_]+/g, " ").trim();
            const short = socialLabelMap[key] || (label ? label[0].toUpperCase() : "?");
            return `
                <a class="social-link" href="${url}" target="_blank" rel="noopener" data-test="social-link-${key}">
                    <span class="social-pill" aria-hidden="true">${short}</span>
                    <span class="visually-hidden">${label}</span>
                </a>`;
        })
        .join("");
}

export const HomeView = {
    template(profile) {
        const data = profile || {};
        const workItems = Array.isArray(data.work_history) ? data.work_history : [];
        const roleTitle = workItems.length ? (workItems[0].role || "") : "";
        const skillTags = Array.isArray(data.skills) ? data.skills : [];
        return `
            <section id="view-home" class="py-5" data-test="view-home">
                <header class="py-5">
                    <div class="container px-5 pb-5">
                        <div class="row gx-5 justify-content-center">
                            <div class="col-12 col-lg-10 col-xxl-8">
                                <div class="hero-card card shadow-sm border-0 rounded-4 overflow-hidden">
                                    <div class="card-body p-4 p-lg-5">
                                        <div class="row g-4 align-items-center">
                                            <div class="col-md-4 text-center">
                                                <div class="profile-circle mx-auto">
                                                    ${data.image_url ? `<img class="profile-img" src="${data.image_url}" alt="Profile image" data-test="profile-image" />` : ""}
                                                </div>
                                            </div>
                                            <div class="col-md-8">
                                                <div class="hero-header">
                                                    <h1 class="profile-name" data-test="profile-name">
                                                        ${data.name || ""}
                                                    </h1>
                                                    ${data.location ? `
                                                        <span class="badge location-badge">
                                                            📍 ${data.location}
                                                        </span>
                                                    ` : ""}
                                                </div>
                                                ${roleTitle ? `<p class="role-title">${roleTitle}</p>` : ""}
                                                <div class="fs-5 fw-light text-muted mb-3 bio" data-test="profile-statement">${data.statement || ""}</div>
                                                ${skillTags.length ? `
                                                    <div class="tags mb-3" data-test="profile-skills">
                                                        ${skillTags.map((s, idx) => `<span class="tag ${idx % 2 ? 'secondary' : ''}">${s}</span>`).join("")}
                                                    </div>
                                                ` : ""}
                                                <div class="socials" data-test="profile-socials">
                                                    ${renderSocialLinks(data.social_links || {})}
                                                </div>
                                            </div>
                                        </div>
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
                                    <h2 class="section-title">Experience</h2>
                                </div>
                                ${workItems
                                    .map((w, idx) => `
                                        <article class="exp-card" data-test="work-card-${idx}">
                                            <div class="exp-meta">
                                                <h3>${w.role || ""}${w.company ? ` @ ${w.company}` : ""}</h3>
                                                <span class="date">${w.start_date || ""} — ${w.end_date || ""}</span>
                                            </div>
                                            ${w.description ? `<ul><li>${w.description}</li></ul>` : ""}
                                            ${Array.isArray(w.skills) && w.skills.length ? `
                                                <div class="tags">
                                                    ${w.skills.map((s, i) => `<span class="tag ${i % 2 ? 'secondary' : ''}">${s}</span>`).join("")}
                                                </div>
                                            ` : ""}
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
