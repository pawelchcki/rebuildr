## Content Addressability of Rebuildr files ( Summary)

Hashes (src-id-.... tags) used in rebuildr follow concepts of content addressability

**Content addressability** means the location or identifier of data is derived from the data itself (typically via a cryptographic hash). If two pieces of data are identical, they share the same address; if they differ by even one bit, they get a different address. This simple property unlocks reliable caching, easy verification, and safe distribution of build artifacts.

### Why it matters for builds
- **Deterministic lookup**: If a build’s inputs are the same, the resulting artifact has the same content hash. You can fetch it directly by its address without guessing how it was produced.
- **Trust and verification**: Because the address is a hash of the content, anyone can verify they fetched the exact artifact intended—no silent drift. (TODO: we should offer the tool ability to inspect content addressable packages)
- **Performance via caching**: Unchanged inputs yield the same artifact address, so previously built artifacts can be re-used instead of rebuilt.
- **Traceability**: One commit sith a set of build inputs  maps to one artifact. This reduces ambiguity in testing, release, and incident response.

### Everyday examples
- **`git`**: Each commit/tree/blob is addressed by a hash of its content. Checking out a commit ID always yields the same files.
- **`Docker`**: Image layers are content-addressed, enabling efficient reuse and distribution.
- **`nix` / `bazel`**: Advanced build systems use content addressability to guarantee reproducible outputs and powerful cache sharing.

### How we apply this
- **One commit and one set of build params → one artifact**: For a given configuration, a single commit ID produces exactly one artifact (e.g., OCI image, wheel, JAR). That artifact is stored once and never overwritten (for now its a honor system, eventually checks will have to be added to enforce this invariance).
- **Deterministic versioning**: The artifact version is derived from a version declared in source plus the commit ID (e.g., replacing a `-dev` suffix with a commit-derived suffix). This avoids CI race conditions and ensures the version uniquely names the content.
- **Downstream simplicity**: Test and release tools can request artifacts by a single value ( content address), enabling bisects, rollbacks, and audits without guesswork.


### Long-term direction
Improving reproducibility (pinning sources, lockfiles, CI config, and Dockerfiles) strengthens content addressability. The more inputs are pinned and hashed, the more reliably we can cache, verify, and share artifacts across teams and environments.
