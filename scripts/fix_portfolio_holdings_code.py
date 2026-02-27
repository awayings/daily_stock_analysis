#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================
Fix portfolio_holdings codes with SH/SZ prefix
===================================

Usage:
    python scripts/fix_portfolio_holdings_code.py
"""

import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage import DatabaseManager, PortfolioHolding
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_portfolio_holdings_code():
    """
    Fix codes in portfolio_holdings that start with SH or SZ prefix (case insensitive).
    - Insert new records with prefix removed
    - Delete original records
    """
    logger.info("=" * 60)
    logger.info("Starting to fix portfolio_holdings codes with SH/SZ prefix")
    logger.info("=" * 60)

    db = DatabaseManager.get_instance()

    with db.get_session() as session:
        all_holdings = session.execute(select(PortfolioHolding)).scalars().all()
        
        holdings_with_prefix = [
            h for h in all_holdings 
            if h.code.upper().startswith('SH') or h.code.upper().startswith('SZ')
        ]

        if not holdings_with_prefix:
            logger.info("No holdings with SH/SZ prefix found, exiting")
            return

        total = len(holdings_with_prefix)
        logger.info(f"Found {total} holdings with SH/SZ prefix")

        inserted_count = 0
        deleted_count = 0
        skipped_count = 0

        for holding in holdings_with_prefix:
            old_code = holding.code
            new_code = old_code[2:]

            existing = session.execute(
                select(PortfolioHolding).where(
                    PortfolioHolding.code == new_code,
                    PortfolioHolding.portfolio_id == holding.portfolio_id
                )
            ).scalars().first()

            if existing:
                logger.warning(f"Skipping {old_code}: record with code {new_code} already exists in portfolio {holding.portfolio_id}")
                skipped_count += 1
                continue

            new_holding = PortfolioHolding(
                portfolio_id=holding.portfolio_id,
                code=new_code,
                name=holding.name,
                entry_price=holding.entry_price,
                last_price=holding.last_price,
                weight=holding.weight,
                shares=holding.shares,
                is_closed=holding.is_closed,
                close_price=holding.close_price,
                close_quantity=holding.close_quantity,
                close_type=holding.close_type,
                added_at=holding.added_at,
                closed_at=holding.closed_at,
                updated_at=holding.updated_at,
            )
            session.add(new_holding)
            session.flush()

            session.delete(holding)

            inserted_count += 1
            deleted_count += 1
            logger.info(f"Fixed: {old_code} -> {new_code}")

        session.commit()

    logger.info("\n" + "=" * 60)
    logger.info("Fix completed")
    logger.info("=" * 60)
    logger.info(f"Total found: {total} holdings")
    logger.info(f"Inserted: {inserted_count}")
    logger.info(f"Deleted: {deleted_count}")
    logger.info(f"Skipped (duplicate): {skipped_count}")


if __name__ == '__main__':
    try:
        fix_portfolio_holdings_code()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        sys.exit(1)
