use masonlinescrap;

create table productos(
nombre varchar(255),
precio double, 
Primary Key(nombre)
);

delimiter $$;
create procedure Sp_registrar_Producto (
in _nombre varchar(255),
in _precio double
)
begin
	if exists (select 1 from productos where nombre = _nombre) then
		update productos
        set precio = _precio
        where nombre = _nombre;
	else
		Insert into productos values (_nombre, _precio);
	end if;
end $$;
delimiter ;
