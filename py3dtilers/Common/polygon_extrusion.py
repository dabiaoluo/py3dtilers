import numpy as np
from ..Common import ObjectToTile
from alphashape import alphashape
from earclip import triangulate


class ExtrudedPolygon():
    def __init__(self, object_to_tile, override_points=False, polygon=None):
        """
        Creates a 3D extrusion of the footprint of an ObjectToTile
        :param object_to_tile: an instance ObjectToTile containing triangles
        :param override_points: when true, the polygon extruded won't be the footprint
        but another polygon
        :param polygon: the polygon that will be extruded instead of the footprint (when overriding points)
        """
        geom_triangles = object_to_tile.geom.triangles
        points = list()
        minZ = np.Inf
        average_maxZ = 0

        # Compute the footprint of the geometry
        for triangles in geom_triangles:
            maxZ = np.NINF
            for triangle in triangles:
                for point in triangle:
                    if len(point) >= 3:
                        points.append([point[0], point[1]])
                        if point[2] < minZ:
                            minZ = point[2]
                        if point[2] > maxZ:
                            maxZ = point[2]
            average_maxZ += maxZ
        average_maxZ /= len(geom_triangles)
        if override_points:
            points = polygon
        else:
            hull = alphashape(points, 0.)
            points = hull.exterior.coords[:-1]

        self.object_to_tile = object_to_tile
        self.points = points
        self.min_height = minZ
        self.max_height = average_maxZ

        self.extrude_footprint()

    def get_extruded_object(self):
        return self.extruded_object

    def extrude_footprint(self):
        coordinates = self.points
        length = len(coordinates)
        vertices = [None] * (2 * length)
        minZ = self.min_height
        maxZ = self.max_height

        for i, coord in enumerate(coordinates):
            vertices[i] = np.array([coord[0], coord[1], minZ], dtype=np.float32)
            vertices[i + length] = np.array([coord[0], coord[1], maxZ], dtype=np.float32)

        # Contains the triangles vertices. Used to create 3D tiles
        triangles = list()

        # Triangulate the feature footprint
        poly_triangles = triangulate(coordinates)

        # Create upper face triangles
        for tri in poly_triangles:
            upper_tri = [np.array([coord[0], coord[1], maxZ], dtype=np.float32) for coord in tri]
            triangles.append(upper_tri)

        # Create side triangles
        for i in range(0, length):
            triangles.append([vertices[i], vertices[length + i], vertices[length + ((i + 1) % length)]])
            triangles.append([vertices[i], vertices[length + ((i + 1) % length)], vertices[((i + 1) % length)]])

        extruded_object = ObjectToTile(str(self.object_to_tile.get_id()) + "_extrude")
        extruded_object.geom.triangles.append(triangles)
        extruded_object.set_box()
        self.extruded_object = extruded_object