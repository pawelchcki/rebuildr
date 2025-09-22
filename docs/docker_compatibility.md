# Docker Compatibility

There are many ways to build docker images. 

The most powerful one is by using buildkit custom drivers, which allow remote and complex builds including ImageContext substitutions.

For now - by default the rebuildr is configured to use `docker buildx build` cli - this is meant to allow easy multiplatform builds.

## Container build compat ideas

In recent years - even in Docker alternatives like Podman or Cri - buildkit has become the shared and best option to build the images.
It should be possible to convert the rebuildr to speak directly to buildkit containers - avoiding having to interface with any specific Docker instance.

Additionally in some contexts users might want to just be able to build and load the images locally - for this the buildkit multiplatform image builds is not ideal.

Building through buildkit requires the final image to have to be loaded into local docker/podman context to be usable. This is not possible for multiplatform images (at least by default on docker, features exists which enable this). So it seems evident we need a way to seamlessly use the most user friendly mode of interfacing with docker. And give the users ability to have more control over multiplatform images, not relying on the default behavior of buildkit et.al.