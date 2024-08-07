# Copyright (c) 2022-2024 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

# syntax=docker/dockerfile:1.2

# Build stage, to create the executable
FROM --platform=$TARGETPLATFORM ghcr.io/eclipse-velocitas/devcontainer-base-images/python:v0.2 as builder
ARG TARGETARCH

RUN apt-get update && apt-get install -y python3-dev \
    # && apt-get install -y binutils \
    && apt-get install -y bash \
    && apt-get install -y pip

COPY ./.velocitas.json /workspace/.velocitas_org.json
COPY ./app /workspace/app

# FIXME: For build tooling we only need "devenv-devcontainer-setup", we should be able to
# filter this without manual jq intervention...
RUN cat ./workspace/.velocitas_org.json | jq 'del(.packages[] | select(.name != "devenv-devcontainer-setup"))' > ./workspace/.velocitas.json

# Remove this installation for Arm64 once staticx has a prebuilt wheel for Arm64
RUN /bin/bash -c 'set -ex && \
    ARCH=`uname -m` && \
    if [ "$ARCH" == "aarch64" ]; then \
    echo "ARM64" && \
    apt-get install -y gcc && \
    pip3 install --no-cache-dir scons; \
    fi'

# RUN pip3 install --no-cache-dir pyinstaller==5.9.0 \
#     && pip3 install --no-cache-dir patchelf==0.17.0.0 \
#     && pip3 install --no-cache-dir staticx \
#     && pip3 install --no-cache-dir -r ./workspace/app/requirements.txt \
#     && pip3 install --no-cache-dir -r ./workspace/app/requirements-links.txt

RUN pip3 install --no-cache-dir -r ./workspace/app/requirements.txt \
    && pip3 install --no-cache-dir -r ./workspace/app/requirements-links.txt

WORKDIR /workspace

RUN velocitas init

# WORKDIR /workspace/app

# RUN pyinstaller --clean -F -s src/main.py

# WORKDIR /workspace/app/dist

# RUN staticx main run-exe

# Runner stage, to copy the executable
#FROM scratch

#COPY --from=builder ./workspace/app/dist/run-exe /dist/

COPY ./app /dist

#ENV PATH="/dist:$PATH"
ENV SDV_MIDDLEWARE_TYPE="native"
ENV SDV_VEHICLEDATABROKER_ADDRESS="grpc://localhost:55555"

# CMD ["bash"]
CMD ["python3","/dist/src/main.py"]
