import pygame
import math

class LaserBeam(pygame.sprite.Sprite):
    def __init__(self, start_point, screen, orientation, mirrors, max_reflections=10):
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()
        self.screen = screen
        self.start_pos = start_point
        self.orientation = orientation
        self.mirrors = mirrors
        self.max_reflections = max_reflections
        self.beam_path = []
        self.compute_beam_path()

    def compute_beam_path(self):
        self.beam_path = [self.start_pos]

        current_point = self.start_pos
        angle_rad = math.radians(self.orientation)
        direction = pygame.Vector2(math.cos(angle_rad), -math.sin(angle_rad))  # Adjust for Pygame's coordinate system

        for _ in range(self.max_reflections):
            closest_intersection_point = None
            min_distance = float('inf')

            # For each mirror, check for intersection
            for mirror in self.mirrors:
                intersection = self.ray_segment_intersect(current_point, direction, mirror.start_pos, mirror.end_pos)
                if intersection:
                    intersection_point, t = intersection
                    distance = (intersection_point - current_point).length()
                    if distance < min_distance:
                        min_distance = distance
                        closest_intersection_point = intersection_point
                        closest_mirror = mirror

            if closest_intersection_point:
                # Found an intersection
                self.beam_path.append(closest_intersection_point)

                # Compute reflected direction
                mirror_direction = (closest_mirror.end_pos - closest_mirror.start_pos).normalize()
                mirror_normal = pygame.Vector2(-mirror_direction.y, mirror_direction.x)  # Perpendicular to mirror

                # Compute reflection: R = D - 2 (D ⋅ N) N
                dot_product = direction.dot(mirror_normal)
                direction = direction - 2 * dot_product * mirror_normal

                current_point = closest_intersection_point
            else:
                # No intersection, extend beam to boundary
                end_point = self.compute_beam_end(current_point, direction)
                self.beam_path.append(end_point)
                break

    def ray_segment_intersect(self, ray_start, ray_direc, line_start, line_end):
        # Small threshold to handle floating-point errors
        epsilon = 1e-6

        line_direc = line_end - line_start
        # Cross product of the direction vectors of the ray and line (mirror)
        denominator = ray_direc.x * line_direc.y - ray_direc.y * line_direc.x

        if abs(denominator) < epsilon:
            # Lines are parallel
            return None

        delta = line_start - ray_start

        t = (delta.x * line_direc.y - delta.y * line_direc.x) / denominator
        s = (delta.x * ray_direc.y - delta.y * ray_direc.x) / denominator

        # Minimum distance to avoid self-intersection
        min_distance_threshold = 1e-3

        if t > epsilon and s >= -epsilon and s <= 1 + epsilon:
            intersection_point = ray_start + t * ray_direc
            distance = (intersection_point - ray_start).length()
            if distance > min_distance_threshold:
                return (intersection_point, t)
        return None


    def compute_beam_end(self, current_point, direction):
        # Screen dimensions
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Table boundary (table occupies rightmost 1/6th of the screen)
        table_boundary_x = screen_width * 5 / 6

        # Initialize a list to hold potential intersection t-values
        t_values = []

        # Left boundary (x = 0)
        if direction.x != 0:
            t_left = (0 - current_point.x) / direction.x
            y_at_t_left = current_point.y + t_left * direction.y
            if t_left > 0 and 0 <= y_at_t_left <= screen_height:
                t_values.append(t_left)

        # Right boundary (x = table_boundary_x)
        if direction.x != 0:
            t_right = (table_boundary_x - current_point.x) / direction.x
            y_at_t_right = current_point.y + t_right * direction.y
            if t_right > 0 and 0 <= y_at_t_right <= screen_height:
                t_values.append(t_right)

        # Top boundary (y = 0)
        if direction.y != 0:
            t_top = (0 - current_point.y) / direction.y
            x_at_t_top = current_point.x + t_top * direction.x
            if t_top > 0 and 0 <= x_at_t_top <= table_boundary_x:
                t_values.append(t_top)

        # Bottom boundary (y = screen_height)
        if direction.y != 0:
            t_bottom = (screen_height - current_point.y) / direction.y
            x_at_t_bottom = current_point.x + t_bottom * direction.x
            if t_bottom > 0 and 0 <= x_at_t_bottom <= table_boundary_x:
                t_values.append(t_bottom)

        if t_values:
            # Choose the smallest positive t-value (closest intersection)
            t_min = min(t_values)
            end_pos = pygame.Vector2(
                current_point.x + t_min * direction.x,
                current_point.y + t_min * direction.y
            )
            return end_pos
        else:
            # If no valid intersection, extend the beam by a large default length
            end_pos = pygame.Vector2(
                current_point.x + 1000 * direction.x,
                current_point.y + 1000 * direction.y
            )
            return end_pos

    def draw(self):
        if len(self.beam_path) < 2:
            return
        for i in range(len(self.beam_path) - 1):
            start_pos = self.beam_path[i]
            end_pos = self.beam_path[i + 1]
            pygame.draw.line(
                self.screen,
                "red",
                start_pos,
                end_pos,
                7  # Adjust the width as needed
            )

    def update(self, dt):
        # Recompute the beam path
        self.compute_beam_path()
