from moderngl_window import WindowConfig
from moderngl_window.geometry.quad import quad_2d
import moderngl
from pathlib import Path
import pyrr
import numpy as np

SCALE = 0.5


class RigidBody2D:
    def __init__(self, mass, moment_of_inertia, position, orientation):
        self.mass = mass
        self.moment_of_inertia = moment_of_inertia
        self.position = np.array(position, dtype=np.float32)
        self.orientation = orientation

        self.linear_velocity = np.zeros(2, dtype=np.float32)
        self.angular_velocity = 0

        self.forces = np.zeros(2, dtype=np.float32)
        self.torques = 0

    def apply_force(self, force, offset):
        rotation_matrix = np.array(
            [
                [np.cos(self.orientation), np.sin(self.orientation)],
                [-np.sin(self.orientation), np.cos(self.orientation)],
            ],
            dtype=np.float32,
        )
        world_force = np.dot(rotation_matrix, force)
        world_offset = np.dot(rotation_matrix, offset)

        self.forces += world_force
        self.torques += np.cross(world_offset, world_force)

    def update(self, dt, gravity=9.8):
        self.linear_velocity += (
            self.forces / self.mass + np.array([0, -gravity], dtype=np.float32)
        ) * dt
        self.position += self.linear_velocity * dt

        self.angular_velocity += self.torques / self.moment_of_inertia * dt
        self.orientation += self.angular_velocity * dt

        self.forces = np.zeros(2, dtype=np.float32)
        self.torques = 0


class DroneSimWindow(WindowConfig):
    resource_dir = Path(__file__).parent / "resources"
    aspect_ratio = 1
    title = "Drone Simulator"
    window_size = (800, 800)
    samples = 4

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pressed_keys = set()

        # rendering a sprite from a png image
        self.sprite_texture = self.load_texture_2d("spaceship.png")
        self.sprite_texture.build_mipmaps()
        self.sprite_texture.anisotropy = 16

        # quad for rendering the sprite
        self.sprite_quad = quad_2d(size=(0.5 * SCALE, 0.5 * SCALE))
        self.sprite_program = self.load_program("sprite.glsl")
        self.sprite_program["spriteTexture"] = 0
        self.sprite_texture.use(location=0)

        # physics
        self.body = RigidBody2D(2.0 * SCALE, 1.0, (0, 0), 0)

    def key_event(self, key, action, modifiers):
        if action == self.wnd.keys.ACTION_PRESS:
            self.pressed_keys.add(key)
        elif action == self.wnd.keys.ACTION_RELEASE:
            self.pressed_keys.discard(key)

    def render(self, time, frametime):
        # enable blending
        self.ctx.enable(moderngl.BLEND)
        self.ctx.clear(0.9, 0.9, 0.9)

        # clamp the position of the drone
        x, y = self.body.position
        x = max(-0.9, min(0.9, x))
        y = max(-0.9, min(0.9, y))

        self.body.position = np.array([x, y])

        # apply forces to the drone
        if self.wnd.keys.D in self.pressed_keys:
            self.body.apply_force((0, 10.0 * SCALE), ((SCALE * -0.7) / 2.0, 0))
        if self.wnd.keys.A in self.pressed_keys:
            self.body.apply_force((0, 10.0 * SCALE), ((SCALE * 0.7) / 2.0, 0))

        if self.wnd.keys.SPACE in self.pressed_keys:
            self.body.apply_force((0, 20.0 * SCALE), (0, 0))

        # update physics
        self.body.update(frametime)
        x, y = self.body.position
        rotation = self.body.orientation

        # create a model matrix
        model = pyrr.matrix44.create_from_z_rotation(rotation)
        model = pyrr.matrix44.multiply(
            model, pyrr.matrix44.create_from_translation(pyrr.Vector3([x, y, 0]))
        )
        self.sprite_program["model"].write(model.astype("f4").tobytes())

        # render sprite
        self.sprite_quad.render(self.sprite_program)


if __name__ == "__main__":
    DroneSimWindow.run()
