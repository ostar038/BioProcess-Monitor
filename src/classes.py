# =======================================================================
# CLASSES
# Define custom classes in this file.
# =======================================================================

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd


class BioprocessMonitor:
    def __init__(self, filepath, ph_lims, temperature_lims):
        """
        Utility class used to monitor bioprocesses by
        generating dashboards and summaries.

        Parameters
        ----------
        filepath : str
            Input CSV dataset path.
        ph_lims : tuple[float, float]
            Lower and upper acceptable pH limits.
        temperature_lims : tuple[float, float]
            Lower and upper acceptable temperature limits.
        """
        self.df = pd.read_csv(filepath)
        self.ph_lims = ph_lims
        self.temperature_lims = temperature_lims

    def extract_batch(self, batch_id):
        """
        Extracts data corresponding to a single batch.

        Parameters
        ----------
        batch_id : int
            Batch identifier.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing only rows associated with
            the requested batch.
        """
        df_batch = self.df[self.df["batch_id"] == batch_id]
        return df_batch.sort_values("time_h").reset_index(drop=True)

    def optimal_ph_mask(self, df_batch):
        """
        Determines whether each pH measurement falls within
        the acceptable operating range.

        Parameters
        ----------
        df_batch : pandas.DataFrame
            Batch-specific DataFrame.

        Returns
        -------
        array-like of bool
            A mask whereby True indicates that the measurement
            is within the acceptable operating range.
        """
        ph_min, ph_max = self.ph_lims
        return df_batch["pH"].between(ph_min, ph_max)

    def optimal_temperature_mask(self, df_batch):
        """
        Determines whether each temperature measurement falls
        within the acceptable operating range.

        Parameters
        ----------
        df_batch : pandas.DataFrame
            Batch-specific DataFrame.

        Returns
        -------
        array-like of bool
            A mask whereby True indicates that the measurement
            is within the acceptable operating range.
        """
        temperature_min, temperature_max = self.temperature_lims
        return df_batch["temperature_C"].between(temperature_min, temperature_max)

    def get_n_batches(self):
        """
        Determines the number of unique batches present
        in the dataset.

        Returns
        -------
        int
            Total number of distinct batch identifiers.
        """
        return int(self.df["batch_id"].nunique())

    def export_dashboard(self, batch_id, filepath):
        """
        Creates and saves a dashboard figure for a single batch.

        Parameters
        ----------
        batch_id : int
            Batch identifier.
        filepath : str
            Output PNG image path.

        Dashboard Requirements
        ----------------------
        Create a 2 × 2 figure containing:

        Top-Left
            Glucose, biomass, and product concentrations versus time.
            - A different color and marker should be used for each substance.

        Top-Right
            Temperature versus time.
            - Measurements within the acceptable temperature range
              should be displayed as green circles.
            - Measurements outside the acceptable temperature range
              should be displayed as red X markers.

        Bottom-Left
            pH versus time.
            - Measurements within the acceptable pH range
              should be displayed as green circles.
            - Measurements outside the acceptable pH range
              should be displayed as red X markers.

        Bottom-Right
            Dissolved oxygen versus time.

        Additional Requirements
        -----------------------
        - Use scatter plots.
        - Add x-axis and y-axis labels.
        - Add legends where appropriate.
        - Apply consistent formatting across all subplots unless
          indicated otherwise.
        - Apply a tick spacing of 6 h on the x-axis for all subplots.
        - Save the figure to the provided filepath.
        - Close the figure after saving.
        """
        df_batch = self.extract_batch(batch_id)
        t = df_batch["time_h"]

        fig, axs = plt.subplots(2, 2, figsize=(12, 8))
        ax_conc, ax_temp = axs[0]
        ax_ph, ax_do = axs[1]

        # Concentrations
        substances = [
            ("C_glucose_g_L^-1", "Glucose", "tab:blue", "o"),
            ("C_biomass_g_L^-1", "Biomass", "tab:orange", "s"),
            ("C_product_g_L^-1", "Product", "tab:purple", "^"),
        ]
        for column, label, color, marker in substances:
            ax_conc.scatter(t, df_batch[column], color=color, marker=marker, label=label)
        ax_conc.set_ylabel("Concentration (g/L)")
        ax_conc.set_title("Concentrations")
        ax_conc.legend()

        # temperature and pH (in range vs out of range)
        range_plots = [
            (ax_temp, "temperature_C", self.optimal_temperature_mask(df_batch),
             self.temperature_lims, "Temperature (°C)", "Temperature"),
            (ax_ph, "pH", self.optimal_ph_mask(df_batch),
             self.ph_lims, "pH", "pH"),
        ]
        for ax, column, mask, lims, ylabel, title in range_plots:
            ax.scatter(t[mask], df_batch[column][mask],
                       color="green", marker="o", label="Within range")
            ax.scatter(t[~mask], df_batch[column][~mask],
                       color="red", marker="x", label="Outside range")
            for lim in lims:
                ax.axhline(lim, color="gray", linestyle="--", linewidth=1)
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.legend()

        # Dissolved oxygen
        ax_do.scatter(t, df_batch["DO_percent"], color="tab:cyan", marker="o")
        ax_do.set_ylabel("Dissolved oxygen (%)")
        ax_do.set_title("Dissolved Oxygen")

        # Formatting
        for ax in axs.flat:
            ax.set_xlabel("Time (h)")
            ax.xaxis.set_major_locator(ticker.MultipleLocator(6))
            ax.grid(True, alpha=0.3)

        fig.suptitle(f"Batch {batch_id}")
        fig.tight_layout()
        fig.savefig(filepath, dpi=150)
        plt.close(fig)

    def export_summary(self, filepath):
        """
        Generates a batch summary table and exports it to a CSV file.

        Parameters
        ----------
        filepath : str
            Output CSV table path.

        Summary Table Columns
        ---------------------
        batch_id
            Batch identifier.

        ph_optimal_percent
            Percentage of measurements in a batch within the
            acceptable pH range, rounded to 2 decimal places.

        temperature_optimal_percent
            Percentage of measurements in a batch within the
            acceptable temperature range, rounded to 2 decimal places.

        C_product_g_L^-1_final
            Final product concentration for the batch.
        """
        rows = []
        for batch_id in sorted(self.df["batch_id"].unique()):
            df_batch = self.extract_batch(batch_id)
            rows.append({
                "batch_id": batch_id,
                "ph_optimal_percent": round(self.optimal_ph_mask(df_batch).mean() * 100, 2),
                "temperature_optimal_percent": round(self.optimal_temperature_mask(df_batch).mean() * 100, 2),
                "C_product_g_L^-1_final": df_batch["C_product_g_L^-1"].iloc[-1],
            })

        pd.DataFrame(rows).to_csv(filepath, index=False)
