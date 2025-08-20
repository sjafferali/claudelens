# Task PRP: Optimize Docker Build with Parallel Execution

## Context

```yaml
context:
  docs:
    - url: https://docs.docker.com/build/ci/github-actions/multi-platform/
      focus: Matrix strategy for parallel builds
    - url: https://github.com/docker/build-push-action
      focus: Build and push action v6 features

  patterns:
    - file: .github/workflows/pr.yml:133-163
      copy: Existing parallel Docker build pattern in PR workflow
    - file: .github/workflows/main.yml:226-267
      copy: Current Docker build implementation

  gotchas:
    - issue: "Matrix builds can overwrite tags"
      fix: "Use digest-based approach with manifest merge"
    - issue: "Cache invalidation between jobs"
      fix: "Use registry cache with proper mode settings"
    - issue: "Temp tag cleanup"
      fix: "Use build-specific tags that get replaced by manifest"
```

## Task Breakdown

### 1. Setup Tasks

**ANALYZE .github/workflows/main.yml:226-332:**
  - OPERATION: Review current Docker build and push jobs
  - VALIDATE: Confirm jobs docker-build and docker-push exist
  - IF_FAIL: Report missing job structure
  - ROLLBACK: N/A - analysis only

**CHECK .github/workflows/main.yml:242-266:**
  - OPERATION: Verify Docker Buildx setup and caching configuration
  - VALIDATE: Confirm cache-from and cache-to are configured
  - IF_FAIL: Note missing cache configuration
  - ROLLBACK: N/A - verification only

### 2. Core Changes - Parallel Build Implementation

**REFACTOR .github/workflows/main.yml:226-267:**
  - OPERATION: Convert docker-build job to use matrix strategy for platforms
  - CHANGES:
    ```yaml
    # Add matrix strategy after line 230
    strategy:
      fail-fast: false
      matrix:
        platform:
          - linux/amd64
          - linux/arm64

    # Update runner selection based on platform
    runs-on: ${{ matrix.platform == 'linux/arm64' && 'ubuntu-latest-arm' || 'ubuntu-latest' }}

    # Modify outputs to include platform-specific digest
    outputs:
      digest: ${{ steps.build.outputs.digest }}
      platform: ${{ matrix.platform }}
    ```
  - VALIDATE: `grep -A 5 "strategy:" .github/workflows/main.yml`
  - IF_FAIL: Check YAML indentation and syntax
  - ROLLBACK: Restore original job configuration

**UPDATE .github/workflows/main.yml:252-266:**
  - OPERATION: Modify build step to output by digest only
  - CHANGES:
    ```yaml
    # Replace tags with digest-only output
    outputs: type=image,name=docker.io/${{ github.repository }},push-by-digest=true,name-canonical=true,push=true
    platforms: ${{ matrix.platform }}
    provenance: false
    ```
  - VALIDATE: Verify build step includes digest output
  - IF_FAIL: Check Docker build-push-action version (must be v6+)
  - ROLLBACK: Restore original build configuration

**ADD .github/workflows/main.yml:after-266:**
  - OPERATION: Export digest to artifact for merge job
  - CHANGES:
    ```yaml
    - name: Export digest
      run: |
        mkdir -p /tmp/digests
        digest="${{ steps.build.outputs.digest }}"
        touch "/tmp/digests/${digest#sha256:}"

    - name: Upload digest
      uses: actions/upload-artifact@v4
      with:
        name: digests-${{ matrix.platform }}
        path: /tmp/digests/*
        if-no-files-found: error
        retention-days: 1
    ```
  - VALIDATE: Check artifact upload configuration
  - IF_FAIL: Verify actions/upload-artifact version
  - ROLLBACK: Remove artifact steps

### 3. Integration - Manifest Merge Job

**REFACTOR .github/workflows/main.yml:268-328:**
  - OPERATION: Update docker-push job to merge manifests from parallel builds
  - CHANGES:
    ```yaml
    needs: [backend-tests, frontend-tests, backend-lint, frontend-lint, security-scan, docker-build]

    steps:
    - name: Download digests
      uses: actions/download-artifact@v4
      with:
        path: /tmp/digests
        pattern: digests-*
        merge-multiple: true

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Docker Hub
      uses: docker/login-action@v3
      with:
        registry: docker.io
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: docker.io/${{ github.repository }}
        tags: |
          type=ref,event=branch
          type=ref,event=tag
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=semver,pattern={{major}}
          type=sha,prefix=,suffix=,format=short
          type=raw,value=latest,enable={{is_default_branch}}

    - name: Create manifest list and push
      working-directory: /tmp/digests
      run: |
        docker buildx imagetools create $(jq -cr '.tags | map("-t " + .) | join(" ")' <<< "$DOCKER_METADATA_OUTPUT_JSON") \
          $(printf 'docker.io/${{ github.repository }}@sha256:%s ' *)
    ```
  - VALIDATE: Confirm manifest creation with `docker manifest inspect`
  - IF_FAIL: Check digest files exist in artifacts
  - ROLLBACK: Restore original push job

### 4. Optimization - Cache Strategy Enhancement

**UPDATE .github/workflows/main.yml:260-262:**
  - OPERATION: Optimize cache configuration for parallel builds
  - CHANGES:
    ```yaml
    cache-from: |
      type=registry,ref=docker.io/${{ github.repository }}:buildcache-${{ matrix.platform }}
      type=registry,ref=docker.io/${{ github.repository }}:buildcache
    cache-to: type=registry,ref=docker.io/${{ github.repository }}:buildcache-${{ matrix.platform }},mode=max
    ```
  - VALIDATE: Verify cache hits in build logs
  - IF_FAIL: Check Docker Hub permissions for cache tags
  - ROLLBACK: Use single cache reference

### 5. Validation Tasks

**TEST .github/workflows/main.yml:**
  - OPERATION: Validate complete workflow syntax
  - VALIDATE: `gh workflow list --all | grep "Main Branch CI/CD"`
  - IF_FAIL: Run `yamllint .github/workflows/main.yml`
  - ROLLBACK: Restore from git

**VERIFY docker-build outputs:**
  - OPERATION: Ensure outputs are properly defined for merge job
  - VALIDATE: Check outputs section includes digest
  - IF_FAIL: Add missing output definitions
  - ROLLBACK: Remove output references

**TEST docker-push dependencies:**
  - OPERATION: Confirm all required jobs in needs array
  - VALIDATE: `grep "needs:" .github/workflows/main.yml`
  - IF_FAIL: Add missing job dependencies
  - ROLLBACK: Restore original needs configuration

### 6. Cleanup Tasks

**REMOVE .github/workflows/main.yml:304-321:**
  - OPERATION: Remove old manifest creation logic
  - VALIDATE: Ensure new manifest creation is in place
  - IF_FAIL: Keep old logic as fallback
  - ROLLBACK: Restore removed lines

**UPDATE .github/workflows/main.yml:332:**
  - OPERATION: Update ci-success job dependencies
  - VALIDATE: All jobs referenced in needs exist
  - IF_FAIL: Fix job name references
  - ROLLBACK: Restore original dependencies

## Validation Strategy

1. **Syntax Validation**: Run `yamllint` after each YAML change
2. **Action Validation**: Use `gh workflow` CLI to validate workflow
3. **Build Testing**: Create test PR to trigger parallel builds
4. **Manifest Verification**: Check multi-arch support with `docker manifest inspect`
5. **Performance Check**: Compare build times before/after optimization

## Risk Assessment

- **Impact**: Medium - affects production deployment pipeline
- **Rollback**: Easy - git revert if issues occur
- **Testing**: Can be validated in PR workflow first
- **Dependencies**: Requires Docker Hub access and GitHub secrets

## Success Criteria

- [ ] Parallel builds complete successfully
- [ ] Build time reduced by >30%
- [ ] Multi-arch manifest created correctly
- [ ] Cache hit rate maintained or improved
- [ ] All existing tags still created
- [ ] No disruption to deployments

## Debug Strategies

1. **Build Failures**: Check platform-specific Dockerfile issues
2. **Digest Missing**: Verify artifact upload/download steps
3. **Manifest Issues**: Use `docker buildx imagetools inspect`
4. **Cache Misses**: Review cache key configuration
5. **Tag Problems**: Verify metadata action output

## Performance Metrics

- Current build time: ~15-20 minutes (sequential)
- Expected build time: ~8-10 minutes (parallel)
- Cache effectiveness: Monitor hit/miss ratio
- Resource usage: Compare runner minutes consumed

## Notes

- Platform list can be extended (linux/arm/v7, etc.)
- Consider using self-hosted runners for arm64 if available
- Registry cache requires sufficient Docker Hub storage
- Provenance must be disabled for multi-platform digest merging
