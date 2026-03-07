import { ComponentFactory } from '../components/ComponentFactory.js';

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
    sortWorkHistory(history) {
        return [...history].sort((a, b) => {
            const dateA = a.end_date === "Present" ? new Date() : new Date(a.end_date || a.start_date);
            const dateB = b.end_date === "Present" ? new Date() : new Date(b.end_date || b.start_date);
            return dateB - dateA;
        });
    },

    template(profile, auth) {
        const data = profile || {};
        const rawWorkItems = Array.isArray(data.work_history) ? data.work_history : [];
        const workItems = HomeView.sortWorkHistory(rawWorkItems);
        
        // Priority Logic for Hero Role Title:
        const currentJob = workItems.find(w => w.end_date && w.end_date.trim() === "Present");
        
        let roleTitle = "";
        if (currentJob) {
            roleTitle = currentJob.role;
        } else if (data.headline_role) {
            roleTitle = data.headline_role;
        } else if (workItems.length > 0) {
            roleTitle = workItems[0].role;
        }
        
        const skillTags = Array.isArray(data.skills) ? data.skills : [];
        return `
            <section id="view-home" class="py-5" data-test="view-home">
                <header class="py-5">
                    <div class="hero-container px-3 px-md-5">
                        <div class="hero-card card shadow-sm border-0 rounded-4 overflow-hidden">
                            <div class="card-body p-4 p-lg-5">
                                <div class="row g-4 align-items-start">
                                    <div class="col-12 col-md-auto text-center">
                                        <div class="profile-circle mx-auto mb-3 mb-md-0" style="width: 160px; height: 160px;">
                                            ${data.image_url ? `<img class="profile-img" src="${data.image_url}" alt="Profile image" data-test="profile-image" />` : ""}
                                        </div>
                                    </div>
                                    <div class="col-12 col-md">
                                        <div class="hero-header mb-3">
                                            <h1 class="profile-name mb-2" data-test="profile-name">
                                                ${data.name || ""}
                                            </h1>
                                            
                                            <div class="d-flex flex-wrap align-items-center gap-3">
                                                ${data.location ? `
                                                    <span class="badge location-badge">
                                                        📍 ${data.location}
                                                    </span>
                                                ` : ""}
                                                
                                                ${data.social_links?.linkedin ? `
                                                    <a href="${data.social_links.linkedin}" target="_blank" class="btn btn-linkedin btn-sm">
                                                        Follow on LinkedIn
                                                    </a>
                                                ` : ""}
                                            </div>
                                        </div>

                                        ${roleTitle ? `<p class="role-title mb-4">${roleTitle}</p>` : ""}
                                        
                                        <div class="fs-5 fw-light text-muted mb-4 bio" data-test="profile-statement" style="line-height: 1.6; max-width: 800px; text-align: justify;">
                                            ${data.statement || ""}
                                        </div>

                                        <div class="d-flex flex-wrap gap-2 mb-4">
                                            ${auth?.hasPermission('profile:manage') ? `
                                                <a class="btn btn-primary btn-sm px-4 rounded-pill shadow-sm" href="/admin/profile">Edit Profile</a>
                                            ` : ""}
                                            ${auth?.hasPermission('content:manage') ? `
                                                <a class="btn btn-outline-dark btn-sm px-4 rounded-pill shadow-sm" href="/admin/articles">Manage Articles</a>
                                            ` : ""}
                                            <a class="btn btn-outline-primary btn-sm px-4 rounded-pill shadow-sm" href="/blog">Technical Blog</a>
                                        </div>

                                        <div class="d-flex flex-wrap align-items-center justify-content-between gap-4 pt-2 border-top">
                                            ${skillTags.length ? `
                                                <div class="tags" data-test="profile-skills">
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
                </header>

                <section class="py-5 bg-light" aria-label="Experience">
                    <div class="wide-container px-3 px-md-5">
                        <div class="text-center mb-5">
                            <h2 class="section-title">Experience</h2>
                        </div>
                        <div class="row justify-content-center">
                            <div class="col-12">
                                ${workItems.map((w, idx) => ComponentFactory.createCard({
                                    title: w.role || "",
                                    subtitle: w.company || "",
                                    meta: `📅 ${w.start_date || ""} — ${w.end_date || ""} &nbsp;&bull;&nbsp; 📍 ${w.location || ""}`,
                                    body: w.description ? `<p class="mb-0">${w.description}</p>` : "",
                                    tags: Array.isArray(w.skills) ? w.skills : [],
                                    dataTest: `work-card-${idx}`
                                })).join("")}
                            </div>
                        </div>
                    </div>
                </section>
            </section>`;
    },
};
