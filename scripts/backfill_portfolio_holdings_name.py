#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================
Backfill portfolio_holdings name field from stock_daily
===================================

Usage:
    python scripts/backfill_portfolio_holdings_name.py
"""

import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage import DatabaseManager, PortfolioHolding, StockDaily
from sqlalchemy import select, func, and_

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_portfolio_holdings_name():
    """
    Backfill name field in portfolio_holdings from stock_daily table.
    Uses case-insensitive code matching.
    """
    logger.info("=" * 60)
    logger.info("Starting to backfill portfolio_holdings name field")
    logger.info("=" * 60)

    db = DatabaseManager.get_instance()

    with db.get_session() as session:
        holdings_without_name = session.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.name.is_(None) | (PortfolioHolding.name == '')
            )
        ).scalars().all()

        if not holdings_without_name:
            logger.info("No holdings without name found, exiting")
            return

        total = len(holdings_without_name)
        logger.info(f"Found {total} holdings without name")

        updated_count = 0
        not_found_count = 0

        for holding in holdings_without_name:
            stock_name = session.execute(
                select(StockDaily.name).where(
                    func.lower(StockDaily.code) == holding.code.lower()
                ).order_by(StockDaily.date.desc()).limit(1)
            ).scalar_one_or_none()

            if stock_name:
                holding.name = stock_name
                updated_count += 1
                logger.debug(f"Updated {holding.code}: {stock_name}")
            else:
                not_found_count += 1
                logger.warning(f"No name found for code: {holding.code}")

        session.commit()

    logger.info("\n" + "=" * 60)
    logger.info("Backfill completed")
    logger.info("=" * 60)
    logger.info(f"Total: {total} holdings")
    logger.info(f"Updated: {updated_count}")
    logger.info(f"Not found: {not_found_count}")


if __name__ == '__main__':
    try:
        backfill_portfolio_holdings_name()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        sys.exit(1)
