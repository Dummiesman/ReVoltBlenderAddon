import math
import bmesh
import io_scene_revolt.common_helpers as common

######################################################
# HELPERS
######################################################
def point_in_bounds(bmin, bmax, p):
    return p[0] >= bmin[0] and p[1] >= bmin[1] and p[0] <= bmax[0] and p[1] <= bmax[1]


def bounds_intersect_3d2d(amin, amax, bmin, bmax):
    return amin[0] <= bmax[0] and amax[0] >= bmin[0] and amin[2] <= bmax[1] and amax[2] >= bmin[1]


def edges_intersect(p1, p2, p3, p4):
    # https://stackoverflow.com/a/24392281
    # returns true if the line from (a,b)->(c,d) intersects with (p,q)->(r,s)
    a, b = p1
    c, d = p2
    p, q = p3
    r, s = p4

    det = (c - a) * (s - q) - (r - p) * (d - b)
    if abs(det) < 0.001:
        return False
    else:
        lmbda = ((s - q) * (r - a) + (p - r) * (s - b)) / det
        gamma = ((b - d) * (r - a) + (c - a) * (s - b)) / det
        return (0 < lmbda and lmbda < 1) and (0 < gamma and gamma < 1)
      

def point_in_polygon(p, vertices):
    n = len(vertices)
    inside =False

    x, y = p
    p1x, p1y = vertices[0]
    for i in range(n+1):
        p2x, p2y = vertices[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/float((p2y-p1y))+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside
  
######################################################
# CLASSES
######################################################
class CollisionBucket:
    def __init__(self, bounds_min, bounds_max, edges, polygon):
        self.edges = edges
        self.bounds = (bounds_min, bounds_max)
        self.polygon = polygon
        self.indices = []
        self.final_indices = []
        
class CollisionGrid:
    def make_from_bmesh(self, bm):
        faces_count = len(bm.faces)
        face_bounds = []
    
        # get min and max bounds
        bnds_min = [float('inf'),float('inf'),float('inf')]
        bnds_max = [float('-inf'),float('-inf'),float('-inf')]
        for face in bm.faces:
            face_bnd = common.face_bounds_rv(face)
            face_bnd_min, face_bnd_max = face_bnd
            face_bounds.append(face_bnd)
            
            for x in range(3):
                bnds_min[x] = min(bnds_min[x], face_bnd_min[x])
                bnds_max[x] = max(bnds_max[x], face_bnd_max[x])
        
        self.bnds_min = bnds_min
        self.bnds_max = bnds_max        
        
        depth_sections = math.ceil((bnds_max[2] - bnds_min[2]) / self.size)
        width_sections = math.ceil((bnds_max[0] - bnds_min[0]) / self.size)
        self.depth_sections = depth_sections
        self.width_sections = width_sections
        
        individual_section_depth = (1 / depth_sections) * (bnds_max[2] - bnds_min[2])
        individual_section_width = (1 / width_sections) * (bnds_max[0] - bnds_min[0])
        
        # create sections structures
        for d in range(depth_sections):
          for w in range(width_sections):
            BOUNDS_INFLATION = 1
            section_bnds_min = ((bnds_min[0] + (w * individual_section_width)) - BOUNDS_INFLATION, (bnds_min[2] + (d * individual_section_depth)) - BOUNDS_INFLATION)
            section_bnds_max = ((bnds_min[0] + ((w + 1) * individual_section_width)) + BOUNDS_INFLATION, (bnds_min[2] + ((d + 1) * individual_section_depth)) + BOUNDS_INFLATION)

            section_edges = (((section_bnds_min[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_min[1])), ((section_bnds_max[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_max[1])),
                             ((section_bnds_min[0], section_bnds_max[1]), (section_bnds_max[0], section_bnds_max[1])), ((section_bnds_min[0], section_bnds_min[1]), (section_bnds_min[0], section_bnds_max[1])))
            section_poly = ((section_bnds_min[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_max[1]), (section_bnds_min[0], section_bnds_max[1]))
           
            # (self, bounds_min, bounds_max, edges, polygon):
            self.buckets.append(CollisionBucket(section_bnds_min, section_bnds_max, section_edges, section_poly))
        
        # loop through faces and find faces in each section
        for face, facenum in zip(bm.faces, range(faces_count)):
          # make a 2d representation of this face
          face_2d = []
          for loop in face.loops:
            vert_revolt = common.vec3_to_revolt(loop.vert.co)
            face_2d.append((vert_revolt[0], vert_revolt[2]))
            
          # get bounds
          face_min, face_max = face_bounds[facenum]
          
          # check each section to see if the face is contained
          for bucket in self.buckets:
            section_bnds_min, section_bnds_max = bucket.bounds
            face_list = bucket.indices
            
            if not bounds_intersect_3d2d(face_min, face_max, section_bnds_min, section_bnds_max):
              continue
              
            isect = False
            
            # face checks
            # check if this polygon surrounds this section
            section_poly = bucket.polygon
            for p in section_poly:
              isect |= point_in_polygon(p, face_2d)
              if isect:
                break
                  
            # edge checks
            if not isect:
              for edge in face.edges:
                if isect:
                    break
                    
                v0_3d = common.vec3_to_revolt(edge.verts[0].co)
                v1_3d = common.vec3_to_revolt(edge.verts[1].co)
                v0 = (v0_3d[0], v0_3d[2])
                v1 = (v1_3d[0], v1_3d[2])
                
                isect |= point_in_bounds(section_bnds_min, section_bnds_max, v0)
                if not isect:
                    isect |= point_in_bounds(section_bnds_min, section_bnds_max, v1)
                
                # more expensive edge-edge intersect testing (only if edge is not vertical)
                edge_is_vertical = v0[0] == v1[0] and v0[1] == v1[1]
                if not isect and not edge_is_vertical:
                    section_edges = bucket.edges
                    for se in section_edges:
                        isect |= edges_intersect(se[0], se[1], v0, v1)
                        if isect:
                            break
                
            if isect:
              face_list.append(facenum)

    def merge_neighbouring_buckets(self):
        # merge neighbouring buckets
        total_sections = self.depth_sections * self.width_sections
        for d in range(self.depth_sections):
          for w in range(self.width_sections):
            bucket = self.buckets[(d * self.width_sections) + w]
            face_list = bucket.indices
            final_face_list = bucket.final_indices
            final_face_list += face_list
            
            for d2 in range(-1, 2):
                for w2 in range(-1, 2):
                    if d2 == 0 and w2 == 0:
                        continue
                
                    other_bucket_index = ((d + d2) * self.width_sections) + (w+w2)
                    if other_bucket_index >= 0 and other_bucket_index < total_sections:
                        other_bucket = self.buckets[other_bucket_index]
                        other_bucket_face_list = other_bucket.indices
                        final_face_list += other_bucket_face_list

            # finally, keep only distinct values
            bucket.final_indices = list(set(final_face_list))

    def finalize(self):
        for bucket in self.buckets:
            bucket.final_indices = []
            bucket.final_indices += bucket.indices
    
    def __init__(self, size):
        self.bnds_min = [0, 0, 0]
        self.bnds_max = [0, 0, 0]
        self.buckets = []
        self.size = size
        self.size_squared = size * size
        self.width_sections = 0
        self.depth_sections = 0