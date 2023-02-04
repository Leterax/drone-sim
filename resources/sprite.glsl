#version 330

#if defined VERTEX_SHADER

in vec3 in_position;
in vec2 in_texcoord_0;
out vec2 uv0;

uniform mat4 model;

void main() {
    // account for position and rotation (2D)
    vec4 pos  = model * vec4(in_position, 1.0);
    gl_Position = pos;
    uv0 = in_texcoord_0;
}

#elif defined FRAGMENT_SHADER

out vec4 fragColor;
uniform sampler2D spriteTexture;
in vec2 uv0;

void main() {
    fragColor = texture(spriteTexture, uv0);
}
#endif