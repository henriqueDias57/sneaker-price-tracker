import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from typing import Optional
from database.db_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger("ChartGenerator")

class ChartGenerator:
    def __init__(self, db_manager: DatabaseManager, output_dir: str = "reports"):
        self.db = db_manager
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self._apply_custom_style()

    @staticmethod
    def _apply_custom_style():
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
        plt.rcParams["font.sans-serif"] = "Segoe UI, Arial, sans-serif"
        plt.rcParams["axes.edgecolor"] = "#E2E8F0"
        plt.rcParams["axes.linewidth"] = 0.8
        plt.rcParams["grid.color"] = "#EDF2F7"
        plt.rcParams["grid.linestyle"] = "--"

    def generate_price_history_chart(self, sneaker_id: Optional[str] = None) -> str:
        df = self.db.get_price_history_dataframe(sneaker_id=sneaker_id)
        if df.empty:
            logger.warning("Sem dados suficientes para gerar gráfico de histórico de preços.")
            return ""

        fig, ax = plt.subplots(figsize=(11, 6), dpi=150)
        colors = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]

        if sneaker_id:
            sneaker_name = f"{df['sneaker_name'].iloc[0]} ({df['colorway'].iloc[0]}) - {df['size'].iloc[0]}"
            ax.set_title(f"Evolução de Preço: {sneaker_name}", fontsize=14, fontweight="bold", pad=15)

            target_price = df["target_price"].iloc[0]
            ax.axhline(y=target_price, color="#DC2626", linestyle=":", linewidth=1.5, label=f"Preço Alvo (R$ {target_price:.2f})")

            for idx, (source, group) in enumerate(df.groupby("source_name")):
                color = colors[idx % len(colors)]
                ax.plot(group["timestamp"], group["price"], marker="o", markersize=4, label=f"Fonte: {source}", color=color, linewidth=2)

        else:
            ax.set_title("Evolução do Histórico de Preços por Modelo (Tamanho BR 40)", fontsize=14, fontweight="bold", pad=15)
            for idx, (s_id, group) in enumerate(df.groupby("sneaker_id")):
                label = f"{group['sneaker_name'].iloc[0]} - {group['colorway'].iloc[0]}"
                color = colors[idx % len(colors)]
                ax.plot(group["timestamp"], group["price"], marker="o", markersize=4, label=label, color=color, linewidth=2)

        ax.set_xlabel("Data / Hora", fontsize=11, labelpad=10)
        ax.set_ylabel("Preço (R$)", fontsize=11, labelpad=10)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M" if df["timestamp"].nunique() > 20 else "%d/%m"))
        fig.autofmt_xdate()

        ax.legend(frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1")
        plt.tight_layout()

        output_path = os.path.join(self.output_dir, f"price_history_{sneaker_id or 'all'}.png")
        plt.savefig(output_path, dpi=150)
        plt.close(fig)

        logger.info(f"Gráfico de histórico salvo em: {output_path}")
        return output_path

    def generate_source_comparison_chart(self) -> str:
        df = self.db.get_price_history_dataframe()
        if df.empty:
            logger.warning("Sem dados suficientes para gerar gráfico de comparação.")
            return ""

        latest_df = df.sort_values("timestamp").groupby(["sneaker_id", "source_name"]).last().reset_index()

        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
        pivot_df = latest_df.pivot(index="sneaker_name", columns="source_name", values="price")

        pivot_df.plot(kind="bar", ax=ax, width=0.6, colormap="tab10")

        ax.set_title("Comparação de Preços Atuais entre Fontes (R$)", fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Modelo de Tênis", fontsize=11, labelpad=10)
        ax.set_ylabel("Preço Atual (R$)", fontsize=11, labelpad=10)
        ax.tick_params(axis="x", rotation=0)

        for p in ax.patches:
            height = p.get_height()
            if not pd.isna(height) and height > 0:
                ax.annotate(
                    f"R$ {height:.0f}",
                    (p.get_x() + p.get_width() / 2., height),
                    ha="center", va="bottom", fontsize=8, xytext=(0, 3),
                    textcoords="offset points"
                )

        ax.legend(title="Fonte", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1")
        plt.tight_layout()

        output_path = os.path.join(self.output_dir, "source_comparison.png")
        plt.savefig(output_path, dpi=150)
        plt.close(fig)

        logger.info(f"Gráfico de comparação de fontes salvo em: {output_path}")
        return output_path
