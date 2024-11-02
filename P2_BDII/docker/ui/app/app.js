// app.js

const { useState,useEffect } = React;
//todo meter esto en una variable de entorno (Nombre del servicio, y el puerto)
const API_URL = 'http://localhost:5005';

function App() {
  const [motor, setMotor] = useState('PostgreSQL');
  const [terminoBusqueda, setTerminoBusqueda] = useState('');
  const [resultados, setResultados] = useState([]);
  const [cancionSeleccionada, setCancionSeleccionada] = useState(null);
  const [filtroLenguaje, setFiltroLenguaje] = useState('');
  const [filtroGenero, setFiltroGenero] = useState('');
  const [filtroPopularidad, setFiltroPopularidad] = useState(0); // Valor mínimo
  const [filtroPopularidadMax, setFiltroPopularidadMax] = useState(100); // Valor máximo
  const [idiomas, setIdiomas] = useState([]);
  const [generos, setGeneros] = useState([]);

  useEffect(() => {
    obtenerDistintos();
  }, []);

  const obtenerDistintos = async () => {
    try {
      const response = await fetch(`${API_URL}/distinct`);
      if (!response.ok) {
        throw new Error('Error al obtener los idiomas y géneros');
      }
      const data = await response.json();
      setIdiomas(data.distinct_languages || []);
      setGeneros(data.distinct_genres || []);
      console.log("Generos e Idiomas cargados...")
    } catch (error) {
      console.error('Error al obtener idiomas y géneros:', error);
    }
  };

  // const obtenerDistintos = async () => {
    
  //     setIdiomas(["pt","en"]);
  //     setGeneros(["rock","cock"]);

  // };

  const manejarBusqueda = async () => {
    try {
      const response = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: terminoBusqueda,
          database: motor === 'PostgreSQL' ? 'postgres' : 'mongo', // Selección de la base de datos
        }),
      });

      if (!response.ok) {
        throw new Error('Error en la búsqueda');
      }

      const data = await response.json();
      
      // Aplicar filtros a los resultados
      let resultadosFiltrados = data;

      // Filtrar por género
      if (filtroGenero && filtroGenero !== 'Todos') {
        console.log("Filtro Genero Habilitado: " + filtroGenero);
        resultadosFiltrados = resultadosFiltrados.filter(cancion => 
          cancion.genres.toLowerCase().includes(filtroGenero.toLowerCase())
        );
      }

      // Filtrar por lenguaje
      if (filtroLenguaje && filtroLenguaje !== 'Todos') {
        console.log("Filtro Lenguaje Habilitado: " + filtroLenguaje)
        resultadosFiltrados = resultadosFiltrados.filter(cancion => 
          cancion.language.toLowerCase() === filtroLenguaje.toLowerCase()
        );
      }

      // Filtrar por popularidad
      if (filtroPopularidad && filtroPopularidadMax) {
        console.log("Filtro Popularidad Habilitado entre " + filtroPopularidad + " y " + filtroPopularidadMax)
        resultadosFiltrados = resultadosFiltrados.filter(cancion => 
          cancion.popularity >= filtroPopularidad && cancion.popularity <= filtroPopularidadMax
        );
      }

      // Mostrar los resultados
      setResultados(resultadosFiltrados); // Guardar los resultados en el estado
      console.log("Mostrando resultados de la búsqueda de canciones...")
    } catch (error) {
      console.error('Error en la búsqueda:', error);
    }
  };

  const seleccionarCancion = (cancion) => {
    setCancionSeleccionada(cancion);
  };

  const resetSeleccion = () => {
    setCancionSeleccionada(null);
  };
  
  return (
    /*--------------------------------------------------------------------------------------*/
    /*--------------------esta es la parte principal, acá se muestra todo-------------------*/
    /*--------------------------------------------------------------------------------------*/
    <div className="contenedor-app">

    {/*-------------------------------------------------------------------------------------*/
    /*-------------este es el header, esta parte no cambia durante la ejecución-------------*/
    /*-------------contiene las cosas en dos contenedores separados por estética------------*/
    /*--------------------------------------------------------------------------------------*/}
      <header className="encabezado-app">

        {/*-------------------------------------------------------------------------------------*/
        /*-----------Título, un slogan inventado y lo principal, la barra de búsqueda-----------*/
        /*--------------------------------------------------------------------------------------*/}
        <div className="parte-principal">
          <h1>TuneStay</h1>
          <p>Tu hogar, al ritmo de tus canciones.</p>

          <div className="barra-busqueda">
            <input 
              type="text" 
              placeholder="Buscar por letra o artista..." 
              value={terminoBusqueda} 
              onChange={(e) => setTerminoBusqueda(e.target.value)} 
            />
            <button onClick={manejarBusqueda}>Buscar</button>
          </div>
        </div>
        
        {/*-------------------------------------------------------------------------------------*/
        /*-----------Todo lo relacionado a los filtros de búsqueda y cambiar el motor-----------*/
        /*--------------------------------------------------------------------------------------*/}
        <div className='parte-filtros'>

          {/*-------------------------------------------------------------------------------------*/
          /*------------------------------------Cambio de motor-----------------------------------*/
          /*--------------------------------------------------------------------------------------*/}
          <div className="controles-busqueda">
            <label>Motor de Búsqueda:</label>
            <select value={motor} onChange={(e) => setMotor(e.target.value)}>
              <option value="PostgreSQL">PostgreSQL</option>
              <option value="Mongo Atlas">Mongo Atlas</option>
            </select>
          </div>

          {/*-------------------------------------------------------------------------------------*/
          /*---------------------------------Filtros de búsqueda----------------------------------*/
          /*--------------------------------------------------------------------------------------*/}
          <div className="filtros">
            <label>Filtrar por Lenguaje:</label>
            <select value={filtroLenguaje} onChange={(e) => setFiltroLenguaje(e.target.value)}>
              <option value="">Todos</option>
              {idiomas.map((idioma, index) => (
                <option key={index} value={idioma}>{idioma}</option>
              ))}
            </select>

            <label>Filtrar por Género:</label>
            <select value={filtroGenero} onChange={(e) => setFiltroGenero(e.target.value)}>
              <option value="">Todos</option>
              {generos.map((genero, index) => (
                <option key={index} value={genero}>{genero}</option>
              ))}
            </select>

            <label>Filtrar por Popularidad:</label>
            <div className="rango-popularidad">
              <input
                type="number"
                min="0"
                max="100" // Puedes ajustar este valor según tus requisitos
                value={filtroPopularidad}
                onChange={(e) => setFiltroPopularidad(Number(e.target.value))}
                placeholder="Mínimo"
              />
              <span> a </span>
              <input
                type="number"
                min="0"
                max="100" // Puedes ajustar este valor según tus requisitos
                value={filtroPopularidadMax}
                onChange={(e) => setFiltroPopularidadMax(Number(e.target.value))}
                placeholder="Máximo"
              />
            </div>
          </div>
        </div>
        
      </header>

      <main className="seccion-resultados">
        {cancionSeleccionada ? (
          <DetallesCancion 
            cancion={cancionSeleccionada} 
            manejarBusqueda={manejarBusqueda} 
            resetSeleccion={resetSeleccion} 
          />
        ) : (
          <ResultadosBusqueda resultados={resultados} onSelect={seleccionarCancion} />
        )}
      </main>
    </div>
  );
}

function ResultadosBusqueda({ resultados, onSelect }) {
  return (
    <div className="lista-resultados">
      <h2>Resultados de Búsqueda</h2>
      {resultados.length > 0 ? (
        resultados.map((cancion, index) => (
          <div key={index} className="item-resultado" onClick={() => onSelect(cancion)}>
            <h3>{cancion.song_name} - {cancion.artist}</h3>
            <p>Género: {cancion.genres}, Popularidad: {cancion.popularity}, Lenguaje: {cancion.language}</p>
          </div>
        ))        
      ) : (
        <p>No se encontraron resultados</p>
      )}
    </div>
  );
}

function DetallesCancion({ cancion, manejarBusqueda, resetSeleccion }) {
  const [apartamentos, setApartamentos] = useState([]);
  const [apartamentoSeleccionado, setApartamentoSeleccionado] = useState(null); // Estado para apartamento seleccionado
  const [letraBusqueda, setLetraBusqueda] = useState('');

  const buscarApartamentos = async () => {
    try {
      const response = await fetch(`${API_URL}/apartment/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          selected_text: letraBusqueda,
        }),
      });

      if (!response.ok) {
        throw new Error('Error en la búsqueda de apartamentos');
      }

      const data = await response.json();
      setApartamentos(data);
      console.log("Mostrando resultados de la búsqueda de apartamentos...")
    } catch (error) {
      console.error('Error en la búsqueda de apartamentos:', error);
    }
  };

  return (
    <div className="detalles-cancion">
      <h2>{cancion.song_name} de {cancion.artist}</h2>
      <p><strong>Género:</strong> {cancion.genres}</p>
      <p><strong>Popularidad:</strong> {cancion.popularity}</p>
      <p><strong>Lenguaje:</strong> {cancion.language}</p>
      <p><strong>Score:</strong> {cancion.score}</p>

      {/*-------------------------------------------------------------------------------------*/
      /*---------------------------Div con scroll Y para la letra---------------------------- */
      /*--------------------------------------------------------------------------------------*/}
      <div style={{ display: 'flex', overflow:'auto'}}>
        <p><strong>Letra:</strong> {cancion.lyric.split('\n').map((linea, index) => (
          <span key={index}>{linea}<br /></span>
        ))}</p>
      </div>
      
      <div className='seccion-busqueda'>
      <textarea 
        rows={4} 
        className='buscar-letra' 
        placeholder='¡Copie y pegue aquí la sección de la letra en base a la que desea buscar!'
        value={letraBusqueda}
        onChange={(e) => setLetraBusqueda(e.target.value)}  // Actualizar el estado
      ></textarea>
        <button onClick={buscarApartamentos}>Buscar apartamentos basados en la letra</button>
      </div>

      {apartamentos.length > 0 && (
        <div style={{ width: '80%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignContent: 'center' }}>
          <h3>Resultados de Apartamentos</h3>
          <div className="lista-resultados" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', width: '100%' }}>
            {apartamentos.map((apto, index) => (
              <div 
                key={index} 
                className="item-resultado" 
                onClick={() => setApartamentoSeleccionado(apto)} // Seleccionar apartamento al hacer clic
              >
                <h4>{apto.name}</h4>
                <p><strong>Resumen:</strong> {apto.summary}</p>
              </div>
            ))}
          </div>

          {/* Mostrar reseñas del apartamento seleccionado */}
          {apartamentoSeleccionado && (
            <div className="reseñas">
              <h4>Descripción completa de {apartamentoSeleccionado.name}:</h4>
              <ul>
                <li>{apartamentoSeleccionado.description}</li>
              </ul>
              <h4>Reseñas de {apartamentoSeleccionado.name}:</h4> {/* Cambiado a 'name' */}
              <ul>
                {apartamentoSeleccionado.reviews.map((resena, idx) => ( // Cambiado a 'reviews'
                  <li key={idx}>{resena}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <button onClick={() => { resetSeleccion(); manejarBusqueda(); }}>Volver a los resultados</button>
    </div>
  );
}

// Renderizar la aplicación
ReactDOM.render(<App />, document.getElementById('root'));