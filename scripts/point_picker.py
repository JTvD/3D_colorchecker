""" Load pointcloud in interactive marking mode
User marks the four corners and presses Q: when done
Repeat this for all squares.
"""
import pandas as pd
import open3d as o3d
import numpy as np
import copy


def pick_points(pcd: o3d.geometry.PointCloud):
    """ Visualize the pointcloud and let the user pick points.
     Returns the list of point indices picked by the user."""
    print("")
    print(
        "1) Please pick at least three correspondences using [shift + left click]"
    )
    print("   Press [shift + right click] to undo point picking")
    print("2) Afther picking points, press q for close the window")
    print("3) Use shift + '+' or '-' to change the marker size")
    # For the other controls see:
    # https://github.com/isl-org/Open3D/blob/d7341c4373e50054d9dbe28ed84c09bb153de2f8/src/Visualization/Visualizer/VisualizerWithEditing.cpp#L124

    vis = o3d.visualization.VisualizerWithEditing()
    vis.create_window()
    vis.add_geometry(pcd)
    vis.run()  # user picks points
    vis.destroy_window()
    print("")
    return vis.get_picked_points()


def extract_colors(pcd: o3d.geometry.PointCloud, marked_points: list):
    """ Extract RGB values of all points within the 2D area (ignoring Z)
        defined by the four selected points."""
    # Get the 4 corner coordinates and ignore Z
    square_corners = np.array(marked_points)
    square_corners_2d = square_corners[:, :2]  # Only X and Y
    points_2d = points[:, :2]

    # Use numpy to check if points are inside the bounding box
    # defined by the four corners (XY only)
    min_xy = np.min(square_corners_2d, axis=0)
    max_xy = np.max(square_corners_2d, axis=0)
    inside_mask = np.all((points_2d >= min_xy) & (points_2d <= max_xy), axis=1)

    colors = np.asarray(pcd.colors)
    inside_points = points[inside_mask]
    inside_colors = colors[inside_mask]
    true_indexes = np.where(inside_mask)[0]
    return inside_points, inside_colors, true_indexes


def generate_topview_image(pcd: o3d.geometry.PointCloud, selected_indexes: list, filename: str):
    """ Render a topview (XY) of the pointcloud using Open3D.
      marking selected points purple
    """

    # Color all points in pcd pink ([1.0, 0.0, 1.0])
    pink = np.array([1.0, 0.0, 1.0])
    colors = np.asarray(pcd.colors)
    colors[selected_indexes] = o3d.utility.Vector3dVector(np.tile(pink,
                                                                  (len(selected_indexes),
                                                                   1)))
    pcd.colors = o3d.utility.Vector3dVector(colors)

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name='Topview (XY) with Selected Points',
                      width=800,
                      height=800, visible=True)
    vis.add_geometry(pcd)
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(f'{filename}.png')
    vis.run()
    print(f'Saved Open3D topview image as {filename}.png')
    vis.destroy_window()


if __name__ == '__main__':
    file = "test_data/pointcloud_b.ply"
    pcd = o3d.io.read_point_cloud(file)
    pcd_copy = copy.deepcopy(pcd)

    while True:
        pcd = copy.deepcopy(pcd_copy)
        points = np.asarray(pcd.points)
        square = pick_points(pcd)

        marked_points = []
        for point_idx in square:
            point = points[point_idx, :]
            marked_points.append(point.tolist())
        print("point_ids:", square)
        print("coordinates: ", marked_points)

        if len(square) != 4:
            print("Warning: not exactly four points selected, \
                  cannot process this as a square!")
            exit(1)

        inside_points, inside_colors, selected_indexes = extract_colors(pcd,
                                                                        marked_points)

        # Ask user for filename and save inside_colors to CSV
        filename = input("Enter filename to save RGB values \
                         (squares are named from A1-D6): ").strip()
        if not filename:
            filename = "output"
        generate_topview_image(pcd, selected_indexes, filename)
        df = pd.DataFrame(inside_colors, columns=["R", "G", "B"])
        df.to_csv(f"{filename}.csv", index=False)
        print(f"Saved RGB values to {filename}.csv")
