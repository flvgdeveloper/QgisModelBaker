# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 23/03/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo (BSF-Swissphoto)
        email                : gcarrillo@linuxmail.org
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

from QgisModelBaker.libili2db.ili2dbutils import get_all_modeldir_in_path
from qgis.PyQt.QtNetwork import QNetworkProxy
from qgis.core import QgsNetworkAccessManager

from ..libili2db.globals import DbIliMode

ili2db_tools = {
    DbIliMode.ili2pg: {
        'version': '3.11.2'
    },
    DbIliMode.ili2gpkg: {
        'version': '3.11.3'
    },
    DbIliMode.ili2mssql: {
        'version': '3.12.2'
    }
}
ili2db_tools[DbIliMode.ili2pg][
    'url'] = 'http://www.eisenhutinformatik.ch/interlis/ili2pg/ili2pg-{}.zip'.format(ili2db_tools[DbIliMode.ili2pg]['version'])
ili2db_tools[DbIliMode.ili2gpkg][
    'url'] = 'http://www.eisenhutinformatik.ch/interlis/ili2gpkg/ili2gpkg-{}.zip'.format(
    ili2db_tools[DbIliMode.ili2gpkg]['version'])
ili2db_tools[DbIliMode.ili2mssql][
    'url'] = 'https://github.com/AgenciaImplementacion/ili2db/releases/download/ili2mssql-{}/ili2mssql.zip'.format(
    ili2db_tools[DbIliMode.ili2mssql]['version'])

class BaseConfiguration(object):

    def __init__(self):
        self.super_pg_user = 'postgres'
        self.super_pg_password = 'postgres'

        self.custom_model_directories_enabled = False
        self.custom_model_directories = ''
        self.java_path = ''
        self.logfile_path = ''

        self.debugging_enabled = False

    def save(self, settings):
        settings.setValue('SuperUser', self.super_pg_user)
        settings.setValue('SuperPassword', self.super_pg_password)
        settings.setValue('CustomModelDirectoriesEnabled',
                          self.custom_model_directories_enabled)
        settings.setValue('CustomModelDirectories',
                          self.custom_model_directories)
        settings.setValue('JavaPath', self.java_path)
        settings.setValue('LogfilePath', self.logfile_path)
        settings.setValue('DebuggingEnabled', self.debugging_enabled)

    def restore(self, settings):
        self.super_pg_user = settings.value(
            'SuperUser', 'postgres', str )
        self.super_pg_password = settings.value(
            'SuperPassword', 'postgres', str )
        self.custom_model_directories_enabled = settings.value(
            'CustomModelDirectoriesEnabled', False, bool)
        self.custom_model_directories = settings.value(
            'CustomModelDirectories', '', str)
        self.java_path = settings.value('JavaPath', '', str)
        self.debugging_enabled = settings.value(
            'DebuggingEnabled', False, bool)
        self.logfile_path = settings.value('LogfilePath', '', str)

    def to_ili2db_args(self, with_modeldir=True):
        """
        Create an ili2db command line argument string from this configuration
        """
        args = list()

        if with_modeldir:
            if self.custom_model_directories_enabled and self.custom_model_directories:
                str_model_directories = [get_all_modeldir_in_path(path) for path in
                                         self.custom_model_directories.split(';')]
                str_model_directories = ';'.join(str_model_directories)
                args += ['--modeldir', str_model_directories]
        if self.debugging_enabled and self.logfile_path:
            args += ['--trace']
            args += ['--log', self.logfile_path]
        return args

    @property
    def model_directories(self):
        dirs = list()
        if self.custom_model_directories_enabled and self.custom_model_directories:
            dirs = self.custom_model_directories.split(';')
        else:
            dirs = [
                '%ILI_FROM_DB',
                '%XTF_DIR',
                'http://models.interlis.ch/',
                '%JAR_DIR'
            ]
        return dirs


class Ili2DbCommandConfiguration(object):
    def __init__(self):
        self.base_configuration = BaseConfiguration()

        self.dbport = ''
        self.dbhost = ''
        self.dbpwd = ''
        self.dbusr = ''
        self.db_use_super_login = False
        self.database = ''
        self.dbschema = ''
        self.dbfile = ''
        self.tool = None
        self.ilifile = ''
        self.ilimodels = ''
        self.tomlfile = ''
        self.dbinstance = ''

    @property
    def uri(self):
        return self._uri(False)

    @property
    def super_user_uri(self):
        return self._uri(True)

    def _uri(self, su = False):
        '''
        The superuser url if su is True - the user configured in the options.
        Otherwise it's the url with the user information entered in the current interface.
        '''
        separator = ' '
        uri = []
        if self.tool == DbIliMode.ili2pg:
            uri += ['dbname={}'.format(self.database)]
            if su:
                uri += ['user={}'.format(self.base_configuration.super_pg_user)]
                if self.base_configuration.super_pg_password:
                    uri += ['password={}'.format(self.base_configuration.super_pg_password)]
            else:
                uri += ['user={}'.format(self.dbusr)]
                if self.dbpwd:
                    uri += ['password={}'.format(self.dbpwd)]
            uri += ['host={}'.format(self.dbhost)]
            if self.dbport:
                uri += ['port={}'.format(self.dbport)]
        elif self.tool == DbIliMode.ili2gpkg:
            uri = [self.dbfile]
        elif self.tool == DbIliMode.ili2mssql:
            uri += ['DRIVER={SQL Server}']
            host = self.dbhost
            if self.dbinstance:
                host += '\\' + self.dbinstance
            if self.dbport:
                host += ',' + self.dbport

            uri += ['SERVER={}'.format(host)]
            uri += ['DATABASE={}'.format(self.database)]
            uri += ['UID={}'.format(self.dbusr)]
            uri += ['PWD={}'.format(self.dbpwd)]
            separator = ';'

        return separator.join(uri)

    def to_ili2db_args(self, hide_password=False):

        # Valid ili file, don't pass --modeldir (it can cause ili2db errors)
        with_modeldir = not self.ilifile

        args = self.base_configuration.to_ili2db_args(with_modeldir=with_modeldir)

        if self.tool == DbIliMode.ili2pg:
            # PostgreSQL specific options
            args += ["--dbhost", self.dbhost]
            if self.dbport:
                args += ["--dbport", self.dbport]
            args += ["--dbusr", self.dbusr]
            if self.dbpwd:
                if hide_password:
                    args += ["--dbpwd", '******']
                else:
                    args += ["--dbpwd", self.dbpwd]
            args += ["--dbdatabase", self.database.strip("'")]
            args += ["--dbschema",
                     self.dbschema or self.database]
        elif self.tool == DbIliMode.ili2gpkg:
            args += ["--dbfile", self.dbfile]
        elif self.tool == DbIliMode.ili2mssql:
            # mssql specific options
            args += ["--dbhost", self.dbhost]
            if self.dbport:
                args += ["--dbport", self.dbport]
            args += ["--dbusr", self.dbusr]
            if self.dbpwd:
                if hide_password:
                    args += ["--dbpwd", '******']
                else:
                    args += ["--dbpwd", self.dbpwd]
            args += ["--dbdatabase", self.database.strip("'")]
            args += ["--dbschema",
                     self.dbschema or self.database]
            if self.dbinstance:
                args+= ["--dbinstance", self.dbinstance]

        proxy = QgsNetworkAccessManager.instance().fallbackProxy()
        if proxy.type() == QNetworkProxy.HttpProxy:
            args += ["--proxy", proxy.hostName()]
            args += ["--proxyPort", str(proxy.port())]

        if self.ilimodels:
            args += ['--models', self.ilimodels]

        if self.tomlfile:
            args += ["--iliMetaAttrs", self.tomlfile]

        if self.ilifile:
            args += [self.ilifile]

        return args


class ExportConfiguration(Ili2DbCommandConfiguration):

    def __init__(self):
        super().__init__()
        self.xtffile = ''
        self.iliexportmodels = ''

    def to_ili2db_args(self, hide_password=False, with_action=True):
        args = list()

        if with_action:
            args += ["--export"]

        if self.iliexportmodels:
            args += ['--exportModels', self.iliexportmodels]

        args += Ili2DbCommandConfiguration.to_ili2db_args(self, hide_password=hide_password)

        args += [self.xtffile]

        return args


class SchemaImportConfiguration(Ili2DbCommandConfiguration):

    def __init__(self):
        super().__init__()
        self.inheritance = 'smart1'
        self.create_basket_col = False
        self.create_import_tid = True
        self.epsg = 21781  # Default EPSG code in ili2pg
        self.stroke_arcs = True

    def to_ili2db_args(self, hide_password=False, with_action=True):
        """
        Create an ili2db argument array, with the password masked with ****** and optionally with the ``action``
        argument (--schemaimport) removed
        """
        args = list()

        if with_action:
            args += ["--schemaimport"]

        args += ["--coalesceCatalogueRef"]
        args += ["--createEnumTabs"]
        args += ["--createNumChecks"]
        args += ["--coalesceMultiSurface"]
        args += ["--coalesceMultiLine"]
        args += ["--coalesceMultiPoint"]
        args += ["--coalesceArray"]
        args += ["--beautifyEnumDispName"]
        args += ["--createUnique"]
        args += ["--createGeomIdx"]
        args += ["--createFk"]
        args += ["--createFkIdx"]
        args += ["--createMetaInfo"]
        args += ["--expandMultilingual"]

        if self.create_import_tid:
            args += ["--importTid"]

        if self.inheritance == 'smart1':
            args += ["--smart1Inheritance"]
        elif self.inheritance == 'smart2':
            args += ["--smart2Inheritance"]
        else:
            args += ["--noSmartMapping"]

        if self.stroke_arcs:
            args += ["--strokeArcs"]

        if self.create_basket_col:
            args += ["--createBasketCol"]

        if self.epsg != 21781:
            args += ["--defaultSrsCode", "{}".format(self.epsg)]

        if self.tool == DbIliMode.ili2pg:
            args += ["--setupPgExt"]

        args += Ili2DbCommandConfiguration.to_ili2db_args(self, hide_password)

        return args


class ImportDataConfiguration(SchemaImportConfiguration):

    def __init__(self):
        super().__init__()
        self.xtffile = ''
        self.delete_data = False

    def to_ili2db_args(self, hide_password=False, with_action=True):
        args = list()

        if with_action:
            args += ["--import"]

        if self.delete_data:
            args += ["--deleteData"]

        args += SchemaImportConfiguration.to_ili2db_args(self, hide_password=hide_password, with_action=False)

        return args
