# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 30/05/17
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

import webbrowser

from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog
from QgisModelBaker.gui.options import OptionsDialog, CompletionLineEdit
from QgisModelBaker.gui.multiple_models import MultipleModelsDialog
from QgisModelBaker.libili2db.globals import displayDbIliMode, DbIliMode
from QgisModelBaker.libili2db.iliimporter import JavaNotFoundError
from QgisModelBaker.libili2db.ilicache import IliCache, ModelCompleterDelegate
from QgisModelBaker.libili2db.ili2dbutils import color_log_text
from QgisModelBaker.libqgsprojectgen.dbconnector import pg_connector
from QgisModelBaker.utils.qt_utils import (
    make_file_selector,
    make_save_file_selector,
    make_folder_selector,
    Validators,
    FileValidator,
    NonEmptyStringValidator,
    OverrideCursor
)
from qgis.PyQt.QtGui import (
    QColor,
    QDesktopServices,
    QValidator
)
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QCompleter
)
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QSettings,
    Qt,
    QLocale
)
from ..utils import get_ui_class
from ..libili2db import (
    iliimporter,
    ili2dbconfig
)
from qgis.gui import QgsGui

DIALOG_UI = get_ui_class('import_data.ui')


class ImportDataDialog(QDialog, DIALOG_UI):

    def __init__(self, base_config, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self);
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.clear()
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.addButton(
            self.tr('Import Data'), QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(QDialogButtonBox.Help)
        self.buttonBox.helpRequested.connect(self.help_requested)
        self.xtf_file_browse_button.clicked.connect(
            make_file_selector(self.xtf_file_line_edit, title=self.tr('Open Transfer or Catalog File'),
                               file_filter=self.tr('Transfer File (*.xtf *.itf);;Catalogue File (*.xml *.xls *.xlsx)')))
        self.gpkg_file_browse_button.clicked.connect(
            make_save_file_selector(self.gpkg_file_line_edit, title=self.tr('Save in GeoPackage database file'),
                                    file_filter=self.tr('GeoPackage Database (*.gpkg)'), extension='.gpkg'))
        self.type_combo_box.clear()
        self.type_combo_box.addItem(self.tr(displayDbIliMode[DbIliMode.pg]), DbIliMode.pg)
        self.type_combo_box.addItem(self.tr(displayDbIliMode[DbIliMode.gpkg]), DbIliMode.gpkg)
        self.type_combo_box.addItem(self.tr(displayDbIliMode[DbIliMode.mssql]), DbIliMode.mssql)
        self.type_combo_box.currentIndexChanged.connect(self.type_changed)
        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)

        self.multiple_models_dialog = MultipleModelsDialog(self)
        self.multiple_models_button.clicked.connect(
            self.multiple_models_dialog.open)
        self.multiple_models_dialog.accepted.connect(
            self.fill_models_line_edit)

        self.base_configuration = base_config
        self.restore_configuration()

        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()
        fileValidator = FileValidator(
            pattern=['*.xtf', '*.itf', '*.pdf', '*.xml', '*.xls', '*.xlsx'])
        gpkgFileValidator = FileValidator(
            pattern='*.gpkg', allow_non_existing=True)

        self.pg_host_line_edit.setValidator(nonEmptyValidator)
        self.pg_database_line_edit.setValidator(nonEmptyValidator)
        self.pg_user_line_edit.setValidator(nonEmptyValidator)
        self.xtf_file_line_edit.setValidator(fileValidator)
        self.gpkg_file_line_edit.setValidator(gpkgFileValidator)

        # mssql fields
        self.mssql_host_line_edit.setValidator(nonEmptyValidator)
        self.mssql_database_line_edit.setValidator(nonEmptyValidator)
        self.mssql_user_line_edit.setValidator(nonEmptyValidator)

        self.ili_models_line_edit.setPlaceholderText(self.tr('[Search model in repository]'))
        self.ili_models_line_edit.textChanged.connect(self.complete_models_completer)
        self.ili_models_line_edit.punched.connect(self.complete_models_completer)
        self.pg_host_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_host_line_edit.textChanged.emit(self.pg_host_line_edit.text())
        self.pg_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_database_line_edit.textChanged.emit(
            self.pg_database_line_edit.text())
        self.pg_user_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_user_line_edit.textChanged.emit(self.pg_user_line_edit.text())
        self.pg_use_super_login.setText(
            self.tr('Generate schema with superuser login from settings ({})').format(base_config.super_pg_user))
        self.xtf_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.xtf_file_line_edit.textChanged.emit(
            self.xtf_file_line_edit.text())
        self.gpkg_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.gpkg_file_line_edit.textChanged.emit(
            self.gpkg_file_line_edit.text())

        # mssql fields
        self.mssql_host_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.mssql_host_line_edit.textChanged.emit(self.mssql_host_line_edit.text())
        self.mssql_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.mssql_database_line_edit.textChanged.emit(self.mssql_host_line_edit.text())
        self.mssql_user_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.mssql_user_line_edit.textChanged.emit(self.mssql_host_line_edit.text())

        settings = QSettings()
        ilifile = settings.value('QgisModelBaker/ili2db/ilifile')
        self.ilicache = IliCache(base_config, ilifile or None)
        self.update_models_completer()
        self.ilicache.refresh()

    def accepted(self):
        configuration = self.updated_configuration()

        if not self.xtf_file_line_edit.validator().validate(configuration.xtffile, 0)[0] == QValidator.Acceptable:
            self.txtStdout.setText(
                self.tr('Please set a valid INTERLIS transfer or catalogue file before importing data.'))
            self.xtf_file_line_edit.setFocus()
            return

        if self.type_combo_box.currentData() == DbIliMode.pg:
            if not configuration.dbhost:
                self.txtStdout.setText(
                    self.tr('Please set a host before importing data.'))
                self.pg_host_line_edit.setFocus()
                return
            if not configuration.database:
                self.txtStdout.setText(
                    self.tr('Please set a database before importing data.'))
                self.pg_database_line_edit.setFocus()
                return
            if not configuration.dbusr:
                self.txtStdout.setText(
                    self.tr('Please set a database user before importing data.'))
                self.pg_user_line_edit.setFocus()
                return
        elif self.type_combo_box.currentData() == DbIliMode.mssql:
            if not configuration.dbhost:
                self.txtStdout.setText(
                    self.tr('Please set a host before importing data.'))
                self.mssql_host_line_edit.setFocus()
                return
            if not configuration.database:
                self.txtStdout.setText(
                    self.tr('Please set a database before importing data.'))
                self.mssql_database_line_edit.setFocus()
                return
            if not configuration.dbusr:
                self.txtStdout.setText(
                    self.tr('Please set a database user before importing data.'))
                self.mssql_user_line_edit.setFocus()
                return
        elif self.type_combo_box.currentData() == DbIliMode.gpkg:
            if not configuration.dbfile or self.gpkg_file_line_edit.validator().validate(configuration.dbfile, 0)[0] != QValidator.Acceptable:
                self.txtStdout.setText(
                    self.tr('Please set a valid database file before creating the project.'))
                self.gpkg_file_line_edit.setFocus()
                return

        # create schema with superuser
        if self.type_combo_box.currentData() == DbIliMode.pg and configuration.db_use_super_login:
            configuration.tool = DbIliMode.ili2pg
            _db_connector = pg_connector.PGConnector(configuration.super_user_uri, configuration.dbschema)
            if not _db_connector.db_or_schema_exists():
                _db_connector.create_db_or_schema(configuration.dbusr)

        with OverrideCursor(Qt.WaitCursor):
            self.progress_bar.show()
            self.progress_bar.setValue(0)

            self.disable()
            self.txtStdout.setTextColor(QColor('#000000'))
            self.txtStdout.clear()

            dataImporter = iliimporter.Importer(dataImport=True)
            dataImporter.tool = self.type_combo_box.currentData()
            dataImporter.configuration = configuration

            self.save_configuration(configuration)

            dataImporter.stdout.connect(self.print_info)
            dataImporter.stderr.connect(self.on_stderr)
            dataImporter.process_started.connect(self.on_process_started)
            dataImporter.process_finished.connect(self.on_process_finished)

            self.progress_bar.setValue(25)

            try:
                if dataImporter.run() != iliimporter.Importer.SUCCESS:
                    self.enable()
                    self.progress_bar.hide()
                    return
            except JavaNotFoundError:
                self.txtStdout.setTextColor(QColor('#000000'))
                self.txtStdout.clear()
                self.txtStdout.setText(self.tr(
                    'Java could not be found. Please <a href="https://java.com/en/download/">install Java</a> and or <a href="#configure">configure a custom java path</a>. We also support the JAVA_HOME environment variable in case you prefer this.'))
                self.enable()
                self.progress_bar.hide()
                return

            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
            self.progress_bar.setValue(100)

    def print_info(self, text, text_color='#000000'):
        self.txtStdout.setTextColor(QColor(text_color))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        color_log_text(text, self.txtStdout)
        self.advance_progress_bar_by_text(text)

    def on_process_started(self, command):
        self.disable()
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.clear()
        self.txtStdout.setText(command)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        color = '#004905' if exit_code == 0 else '#aa2222'
        self.txtStdout.setTextColor(QColor(color))
        self.txtStdout.append('Finished ({})'.format(exit_code))
        if result == iliimporter.Importer.SUCCESS:
            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
        else:
            self.enable()

    def updated_configuration(self):
        """
        Get the configuration that is updated with the user configuration changes on the dialog.
        :return: Configuration
        """
        configuration = ili2dbconfig.ImportDataConfiguration()

        if self.type_combo_box.currentData() == DbIliMode.pg:
            # PostgreSQL specific options
            configuration.dbhost = self.pg_host_line_edit.text().strip()
            configuration.dbport = self.pg_port_line_edit.text().strip()
            configuration.dbusr = self.pg_user_line_edit.text().strip()
            configuration.database = self.pg_database_line_edit.text().strip()
            configuration.dbschema = self.pg_schema_line_edit.text().strip().lower()
            configuration.dbpwd = self.pg_password_line_edit.text()
            configuration.db_use_super_login = self.pg_use_super_login.isChecked()
        elif self.type_combo_box.currentData() == DbIliMode.gpkg:
            configuration.dbfile = self.gpkg_file_line_edit.text().strip()
        elif self.type_combo_box.currentData() == DbIliMode.mssql:
            configuration.dbhost = self.mssql_host_line_edit.text().strip()
            configuration.dbinstance = self.mssql_instance_line_edit.text().strip()
            configuration.dbport = self.mssql_port_line_edit.text().strip()
            configuration.dbusr = self.mssql_user_line_edit.text().strip()
            configuration.database = self.mssql_database_line_edit.text().strip()
            configuration.dbschema = self.mssql_schema_line_edit.text().strip().lower()
            configuration.dbpwd = self.mssql_password_line_edit.text()

        configuration.xtffile = self.xtf_file_line_edit.text().strip()
        configuration.delete_data = self.chk_delete_data.isChecked()
        configuration.ilimodels = self.ili_models_line_edit.text().strip()
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()
        configuration.base_configuration = self.base_configuration

        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue(
            'QgisModelBaker/ili2pg/xtffile_import', configuration.xtffile)
        settings.setValue(
            'QgisModelBaker/ili2pg/deleteData', configuration.delete_data)
        settings.setValue(
            'QgisModelBaker/importtype', self.type_combo_box.currentData())

        if self.type_combo_box.currentData() & DbIliMode.pg:
            # PostgreSQL specific options
            settings.setValue('QgisModelBaker/ili2pg/host',
                              configuration.dbhost)
            settings.setValue('QgisModelBaker/ili2pg/port',
                              configuration.dbport)
            settings.setValue('QgisModelBaker/ili2pg/user',
                              configuration.dbusr)
            settings.setValue('QgisModelBaker/ili2pg/database',
                              configuration.database)
            settings.setValue('QgisModelBaker/ili2pg/schema',
                              configuration.dbschema)
            settings.setValue('QgisModelBaker/ili2pg/password',
                              configuration.dbpwd)
            settings.setValue('QgisModelBaker/ili2pg/usesuperlogin',
                              configuration.db_use_super_login)
        elif self.type_combo_box.currentData() & DbIliMode.gpkg:
            settings.setValue('QgisModelBaker/ili2gpkg/dbfile',
                              configuration.dbfile)
        elif self.type_combo_box.currentData() & DbIliMode.mssql:
            settings.setValue(
                'QgisModelBaker/ili2mssql/host', configuration.dbhost)
            settings.setValue(
                'QgisModelBaker/ili2mssql/instance', configuration.dbinstance)
            settings.setValue(
                'QgisModelBaker/ili2mssql/port', configuration.dbport)
            settings.setValue('QgisModelBaker/ili2mssql/user', configuration.dbusr)
            settings.setValue(
                'QgisModelBaker/ili2mssql/database', configuration.database)
            settings.setValue(
                'QgisModelBaker/ili2mssql/schema', configuration.dbschema)
            settings.setValue('QgisModelBaker/ili2mssql/password', configuration.dbpwd)

    def restore_configuration(self):
        settings = QSettings()

        self.fill_toml_file_info_label()
        self.xtf_file_line_edit.setText(settings.value(
            'QgisModelBaker/ili2pg/xtffile_import'))
        self.chk_delete_data.setChecked(settings.value(
            'QgisModelBaker/ili2pg/deleteData', False, bool))
        self.pg_host_line_edit.setText(settings.value(
            'QgisModelBaker/ili2pg/host', 'localhost'))
        self.pg_port_line_edit.setText(settings.value(
            'QgisModelBaker/ili2pg/port'))
        self.pg_user_line_edit.setText(settings.value(
            'QgisModelBaker/ili2pg/user'))
        self.pg_database_line_edit.setText(settings.value(
            'QgisModelBaker/ili2pg/database'))
        self.pg_schema_line_edit.setText(settings.value(
            'QgisModelBaker/ili2pg/schema'))
        self.pg_password_line_edit.setText(settings.value(
            'QgisModelBaker/ili2pg/password'))
        self.pg_use_super_login.setChecked(settings.value(
            'QgisModelBaker/ili2pg/usesuperlogin', defaultValue=False, type=bool))
        self.gpkg_file_line_edit.setText(settings.value(
            'QgisModelBaker/ili2gpkg/dbfile'))

        self.mssql_host_line_edit.setText(settings.value(
            'QgisModelBaker/ili2mssql/host', 'localhost'))
        self.mssql_instance_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/instance'))
        self.mssql_port_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/port'))
        self.mssql_user_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/user'))
        self.mssql_database_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/database'))
        self.mssql_schema_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/schema'))
        self.mssql_password_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/password'))

        mode = settings.value('QgisModelBaker/importtype', DbIliMode.pg)
        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(~DbIliMode.ili & mode)) # Get the base mode, without the ili
        self.type_changed()

    def disable(self):
        self.pg_config.setEnabled(False)
        self.ili_config.setEnabled(False)
        self.buttonBox.setEnabled(False)

    def enable(self):
        self.pg_config.setEnabled(True)
        self.ili_config.setEnabled(True)
        self.buttonBox.setEnabled(True)

    def type_changed(self):
        self.progress_bar.hide()
        self.pg_config.hide()
        self.gpkg_config.hide()
        self.mssql_config.hide()

        if self.type_combo_box.currentData() == DbIliMode.pg:
            self.pg_config.show()
        elif self.type_combo_box.currentData() == DbIliMode.gpkg:
            self.gpkg_config.show()
        elif self.type_combo_box.currentData() == DbIliMode.mssql:
            self.mssql_config.show()

    def link_activated(self, link):
        if link.url() == '#configure':
            cfg = OptionsDialog(self.base_configuration)
            if cfg.exec_():
                settings = QSettings()
                settings.beginGroup('QgisModelBaker/ili2db')
                self.base_configuration.save(settings)
        else:
            QDesktopServices.openUrl(link)

    def complete_models_completer(self):
        if not self.ili_models_line_edit.text():
            self.ili_models_line_edit.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            self.ili_models_line_edit.completer().complete()
        else:
            self.ili_models_line_edit.completer().setCompletionMode(QCompleter.PopupCompletion)

    def update_models_completer(self):
        completer = QCompleter(self.ilicache.model, self.ili_models_line_edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.delegate = ModelCompleterDelegate()
        completer.popup().setItemDelegate(self.delegate)
        self.ili_models_line_edit.setCompleter(completer)
        self.multiple_models_dialog.models_line_edit.setCompleter(completer)

    def fill_models_line_edit(self):
        self.ili_models_line_edit.setText(
            self.multiple_models_dialog.get_models_string())

    def fill_toml_file_info_label(self):
        text = None
        if self.ili2db_options.toml_file():
            text = self.tr('Extra Model Information File: {}').format(('…'+self.ili2db_options.toml_file()[len(self.ili2db_options.toml_file())-40:]) if len(self.ili2db_options.toml_file()) > 40 else self.ili2db_options.toml_file())
        self.toml_file_info_label.setText(text)
        self.toml_file_info_label.setToolTip(self.ili2db_options.toml_file())

    def help_requested(self):
        os_language = QLocale(QSettings().value(
            'locale/userLocale')).name()[:2]
        if os_language in ['es', 'de']:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/{}/user-guide.html#import-an-interlis-transfer-file-xtf".format(os_language))
        else:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/user-guide.html#import-an-interlis-transfer-file-xtf")

    def advance_progress_bar_by_text(self, text):
        if text.strip() == 'Info: compile models...':
            self.progress_bar.setValue(50)
            QCoreApplication.processEvents()
        elif text.strip() == 'Info: create table structure...':
            self.progress_bar.setValue(75)
            QCoreApplication.processEvents()
