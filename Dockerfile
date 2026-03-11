# lambda AL2023 base
FROM public.ecr.aws/lambda/python:3.12

# ---- system deps required by Chromium/Playwright on AL2023 ----
RUN dnf -y update && dnf -y install \
    # core graphics / X11 libs
    libX11 libXcomposite libXdamage libXext libXfixes libXrandr libXcursor libXrender libXtst \
    # rendering / text / a11y
    pango cairo atk at-spi2-atk at-spi2-core \
    # media / printing / audio
    nss nspr cups-libs alsa-lib \
    # GPU / headless
    libdrm mesa-libgbm \
    # input / wayland helpers often needed by recent Chromium builds
    libxkbcommon libwayland-client libwayland-server \
    # fonts (avoid tofu/missing glyphs)
    dejavu-sans-fonts liberation-fonts \
    # utils
    tar gzip unzip ca-certificates \
 && dnf clean all

RUN dnf -y install dbus-libs && dnf clean all

# ---- KEY: install browsers into a fixed path inside the image ----
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV DBUS_SESSION_BUS_ADDRESS=/dev/null
ENV DBUS_SYSTEM_BUS_ADDRESS=/dev/null

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# install Chromium into /ms-playwright and make it readable by Lambda user
RUN python -m playwright install chromium && chmod -R 0755 /ms-playwright

# app code
COPY . ${LAMBDA_TASK_ROOT}

# lambda entrypoint
CMD ["handler.lambda_handler"]
