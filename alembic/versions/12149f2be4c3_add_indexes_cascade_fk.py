"""add_indexes_cascade_fk

Revision ID: 12149f2be4c3
Revises: 
Create Date: 2026-06-27 08:42:34.612085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '12149f2be4c3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes (skip if already exists from partial run)
    op.execute("CREATE INDEX IF NOT EXISTS ix_price_product_date ON price_records (product_id, record_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_benchmark_product_date ON benchmark_prices (product_id, record_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_detailed_product_date ON detailed_quotes (product_id, publish_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alert_config_product ON alert_configs (product_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alert_record_product ON alert_records (product_id)")

    # SQLite batch mode for FK constraint changes
    with op.batch_alter_table('product_categories') as batch_op:
        batch_op.create_foreign_key('fk_pc_product', 'products', ['product_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_pc_category', 'categories', ['category_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('categories') as batch_op:
        batch_op.create_foreign_key('fk_cat_parent', 'categories', ['parent_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('price_records') as batch_op:
        batch_op.create_foreign_key('fk_pr_product', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('benchmark_prices') as batch_op:
        batch_op.create_foreign_key('fk_bp_product', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('detailed_quotes') as batch_op:
        batch_op.create_foreign_key('fk_dq_product', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('alert_configs') as batch_op:
        batch_op.create_foreign_key('fk_ac_product', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('alert_records') as batch_op:
        batch_op.create_foreign_key('fk_ar_config', 'alert_configs', ['alert_config_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_ar_product', 'products', ['product_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    with op.batch_alter_table('alert_records') as batch_op:
        batch_op.drop_index('ix_alert_record_product')
        batch_op.drop_constraint('fk_ar_config', type_='foreignkey')
        batch_op.drop_constraint('fk_ar_product', type_='foreignkey')

    with op.batch_alter_table('alert_configs') as batch_op:
        batch_op.drop_index('ix_alert_config_product')
        batch_op.drop_constraint('fk_ac_product', type_='foreignkey')

    with op.batch_alter_table('detailed_quotes') as batch_op:
        batch_op.drop_index('ix_detailed_product_date')
        batch_op.drop_constraint('fk_dq_product', type_='foreignkey')

    with op.batch_alter_table('benchmark_prices') as batch_op:
        batch_op.drop_index('ix_benchmark_product_date')
        batch_op.drop_constraint('fk_bp_product', type_='foreignkey')

    with op.batch_alter_table('price_records') as batch_op:
        batch_op.drop_index('ix_price_product_date')
        batch_op.drop_constraint('fk_pr_product', type_='foreignkey')

    with op.batch_alter_table('categories') as batch_op:
        batch_op.drop_constraint('fk_cat_parent', type_='foreignkey')

    with op.batch_alter_table('product_categories') as batch_op:
        batch_op.drop_constraint('fk_pc_product', type_='foreignkey')
        batch_op.drop_constraint('fk_pc_category', type_='foreignkey')
