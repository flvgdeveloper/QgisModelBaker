# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    08/04/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania
    email                :    yesidpol.3@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from .db_factory import DbFactory
from .pg_factory import PgFactory
from .gpkg_factory import GpkgFactory
from .mssql_factory import MssqlFactory
from QgisModelBaker.libili2db.globals import DbIliMode


class DbSimpleFactory:
    """Provides a single point (simple factory) to create a database factory (:class:`DbFactory`).
    """

    _available_databases = [DbIliMode.pg, DbIliMode.gpkg, DbIliMode.mssql]
    _index_default_db = 0

    def create_factory(self, ili_mode: DbIliMode) -> DbFactory:
        """Creates an instance of :class:`DbFactory` based on ili_mode parameter.

        :param ili_mode: Value specifying which factory will be instantiated.
        :type ili_mode: :class:`DbIliMode`
        :return: A database factory
        """
        if not ili_mode:
            return None

        result = None

        if ili_mode & DbIliMode.pg:
            result = PgFactory()
        elif ili_mode & DbIliMode.gpkg:
            result = GpkgFactory()
        elif ili_mode & DbIliMode.mssql:
            result = MssqlFactory()

        return result

    def get_db_list(self, is_schema_import=False):
        """Gets a list containing the databases available in QgisModelBaker.

        This list can be used to show the available databases in GUI, for example, **QComboBox source**
        in **Import Data Dialog**.

        :param bool is_schema_import: *True* to include interlis operation values, *False* otherwise.
        :return: A list containing the databases available.
        :rtype: list
        """
        ili = []
        result = self._available_databases.copy()

        if is_schema_import:
            for item in result:
                ili += [item | DbIliMode.ili]

            result = ili + result

        return result

    @property
    def default_database(self):
        """Gets a default database for QgisModelBaker.

        :return: Default database for QgisModelBaker.
        :rtype: :class:`DbIliMode`
        """
        return self._available_databases[self._index_default_db]
