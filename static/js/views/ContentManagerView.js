export const ContentManagerView = {
    template() {
        return `
            <section id="view-content-manager" class="py-5" data-test="view-content-manager">
                <div class="container px-5">
                    <header class="mb-4 text-center">
                        <h2 class="display-6 fw-bolder">Content Manager</h2>
                        <p class="text-muted mb-0">Manage your articles</p>
                    </header>
                    <div class="row gx-4" data-test="content-manager-grid">
                        <div class="col-md-4 mb-4">
                            <div class="card h-100 border-0 shadow-sm">
                                <div class="card-body">
                                    <h5 class="card-title">Create Article</h5>
                                    <p class="card-text">Start a new article draft.</p>
                                    <button class="btn btn-outline-primary w-100" type="button" data-test="create-article">
                                        New Article
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="card h-100 border-0 shadow-sm">
                                <div class="card-body">
                                    <h5 class="card-title">Edit Articles</h5>
                                    <p class="card-text">Review and update existing content.</p>
                                    <button class="btn btn-outline-secondary w-100" type="button" data-test="edit-articles">
                                        View Articles
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="card h-100 border-0 shadow-sm">
                                <div class="card-body">
                                    <h5 class="card-title">Publish</h5>
                                    <p class="card-text">Publish drafts to the public blog.</p>
                                    <button class="btn btn-outline-success w-100" type="button" data-test="publish-articles">
                                        Publish
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <section class="mt-4" data-test="content-manager-table">
                        <div class="card border-0 shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title mb-3">Articles</h5>
                                <div class="table-responsive">
                                    <table class="table align-middle">
                                        <thead>
                                            <tr>
                                                <th scope="col">Title</th>
                                                <th scope="col">Status</th>
                                                <th scope="col">Updated</th>
                                                <th scope="col" class="text-end">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td>Example Article</td>
                                                <td><span class="badge bg-secondary">Draft</span></td>
                                                <td>—</td>
                                                <td class="text-end">
                                                    <button class="btn btn-sm btn-outline-primary" type="button">Edit</button>
                                                    <button class="btn btn-sm btn-outline-danger" type="button">Delete</button>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </section>
                </div>
            </section>`;
    },
};
