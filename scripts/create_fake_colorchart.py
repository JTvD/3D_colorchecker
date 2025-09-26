"""Example of how a colorchecker template can be filled with values
   extracted from a pointcloud."""
import numpy as np
import pandas as pd
import cv2
import os


def infer_d6(color_df: pd.DataFrame, data_folder: str):
    """ Infer the RGB values for D6 based on a linear gradient from D1 to D5.
    """
    x = []
    y = []
    for col in range(1, 6):
        x.append(color_df[(color_df['row'] == 'D') &
                          (color_df['col'] == col)]['R'].values[0].item())
        rgb_values = pd.read_csv(f'{data_folder}/D{col}.csv')
        # Scale to 0-255
        rgb_values = rgb_values[['R', 'G', 'B']].values * 255
        y.append(rgb_values.mean(axis=0).astype(int))

    # Linear fit: y = m*x + b for each channel and print R2
    y = np.array(y)  # shape (5, 3)
    x = np.array(x)
    m = []
    b = []
    r2 = []
    for i, channel in enumerate(['R', 'G', 'B']):
        coeffs = np.polyfit(x, y[:, i], 1)
        m.append(coeffs[0])
        b.append(coeffs[1])
        y_fit = m[-1] * x + b[-1]
        ss_res = np.sum((y[:, i] - y_fit) ** 2)
        ss_tot = np.sum((y[:, i] - np.mean(y[:, i])) ** 2)
        r2_val = 1 - (ss_res / ss_tot) if ss_tot != 0 else float('nan')
        r2.append(r2_val)
        print(f"R² of fit for {channel}: {r2_val:.3f}")

    x_pred = color_df[(color_df['row'] == 'D') & (color_df['col'] == 6)][['R']].values[0]
    prediction = m * x_pred + b
    # Color values cannot be negative
    prediction = np.maximum(prediction, 0)

    print("Predicted R for D6:", prediction)
    return prediction.astype(int)


if __name__ == '__main__':
    # Load the template image
    colorchecker = cv2.imread('color_checker/color_checker_ref.png')

    # TODO: update the path to the location with real data
    datafolder = 'test_data'

    # Load the RGB values from the CSV file
    df = pd.read_csv('color_checker/color_checker_values.csv')

    # Squares are named for A1 to D6.
    for _, row in df.iterrows():
        square_id = row['row'] + str(row['col'])
        data_file = f'{datafolder}/{square_id}.csv'

        if square_id == 'D6' and not os.path.exists(data_file):
            print("No data found for D6, applying linear gradient")
            avg_color = infer_d6(df, datafolder)
            rgb_values = np.array([avg_color] * 3)

        elif not os.path.exists(data_file):
            print(f"Warning: {data_file} does not exist. Skipping {square_id}.")
        else:
            rgb_values = pd.read_csv(data_file)
            # Scale to 0-255
            rgb_values = rgb_values[['R', 'G', 'B']].values * 255
        avg_color = rgb_values.mean(axis=0).astype(int)

        # note, opencv uses BGR order!
        mask = np.all(colorchecker == (row['B'], row['G'], row['R']), axis=-1)
        colorchecker[mask] = avg_color[::-1]

    # Save the modified image
    cv2.imwrite('fake_color_checker.png', colorchecker)
